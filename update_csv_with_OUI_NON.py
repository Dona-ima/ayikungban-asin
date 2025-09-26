import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon
import json
import os

# === Paramètres ===
INPUT_CSV = "submission.csv"
DOSSER_COUCHE = "couche"
SEP = ";"           # adapte si nécessaire
ENC = "utf-8-sig"   # enleve BOM si présent

# === Lecture CSV ===
df = pd.read_csv(INPUT_CSV, encoding=ENC, sep=SEP)
print("Colonnes trouvées :", df.columns.tolist())

# === Conversion Coordonnées -> Polygon (robuste) ===
def coords_to_polygon(cell):
    # Retourne une shapely Polygon ou None si invalide / vide
    if pd.isna(cell):
        return None
    # Si déjà structure Python (list/dict) : gère directement
    try:
        if isinstance(cell, (list, tuple)):
            coords = cell
        elif isinstance(cell, dict):
            coords = [cell]
        else:
            # strip string
            s = str(cell).strip()
            if s == "" or s.lower() in ("nan", "none", "null"):
                return None
            # essayer JSON
            try:
                coords = json.loads(s)
            except Exception:
                # essai fallback: literal_eval (au cas où c'est une repr Python)
                import ast
                try:
                    coords = ast.literal_eval(s)
                except Exception:
                    return None
        # coords doit être une liste de dicts avec ['x','y'] ou liste de tuples
        pts = []
        for c in coords:
            if isinstance(c, dict) and 'x' in c and 'y' in c:
                pts.append((float(c['x']), float(c['y'])))
            elif isinstance(c, (list, tuple)) and len(c) >= 2:
                pts.append((float(c[0]), float(c[1])))
            else:
                # entrée non reconnue -> ignorer
                continue
        if len(pts) < 3:
            return None
        return Polygon(pts)
    except Exception as e:
        print("Erreur coords_to_polygon:", e, "->", cell)
        return None

# Créer la colonne geometry
df['geometry'] = df['Coordonnées'].apply(coords_to_polygon)

# Convertir en GeoDataFrame avec le bon CRS (UTM Zone 31N)
gdf = gpd.GeoDataFrame(df, geometry='geometry', crs="EPSG:32631")

# === Dictionnaire des couches ===
layers = {
    "aif": "aif.geojson",
    "air_proteges": "air_proteges.geojson",
    "dpl": "dpl.geojson",
    "dpm": "dpm.geojson",
    "enregistrement individuel": "enregistrement individuel.geojson",
    "litige": "litige.geojson",
    "parcelles": "parcelles.geojson",
    "restriction": "restriction.geojson",
    "tf_demembres": "tf_demembres.geojson",
    "tf_en_cours": "tf_en_cours.geojson",
    "tf_etat": "tf_etat.geojson",
    "titre_reconstitue": "titre_reconstitue.geojson",
    "zone_inondable": "zone_inondable.geojson"
}

# === Fonction utilitaire pour union (avec plusieurs niveaux de fallback) ===
def compute_union(gdf_layer):
    try:
        # Premier essai : tenter de rendre les géométries valides
        valid_geoms = gdf_layer.geometry.make_valid()
        return valid_geoms.union_all()
    except Exception as e:
        print(f"Attention : union_all a échoué ({e}), tentative de méthode alternative...")
        try:
            # Deuxième essai : tenter unary_union avec géométries valides
            valid_geoms = gdf_layer.geometry.make_valid()
            return valid_geoms.unary_union
        except Exception as e:
            print(f"Attention : unary_union a échoué ({e}), utilisation de buffer(0) pour réparer les géométries...")
            try:
                # Troisième essai : tenter de réparer les géométries avec buffer(0)
                fixed_geoms = gdf_layer.geometry.buffer(0)
                return fixed_geoms.union_all()
            except Exception as e:
                print(f"Erreur : toutes les tentatives d'union ont échoué ({e})")
                return None

# === Boucle : traiter uniquement les lignes avec géométrie et colonnes vides ===
for col, fname in layers.items():
    layer_path = os.path.join(DOSSER_COUCHE, fname)
    print(f"\n--- Traitement couche '{col}' depuis '{layer_path}' ---")
    if not os.path.exists(layer_path):
        print(f"⚠️ Fichier absent : {layer_path}. On passe.")
        continue

    # Charger couche
    try:
        gdf_layer = gpd.read_file(layer_path)
    except Exception as e:
        print("Erreur lecture couche:", e)
        continue

    if gdf_layer.empty:
        print("⚠️ Couche vide :", layer_path)
        continue

    # Reprojeter si nécessaire
    try:
        if gdf_layer.crs is not None and gdf_layer.crs != gdf.crs:
            gdf_layer = gdf_layer.to_crs(gdf.crs)
    except Exception as e:
        print("Erreur reprojection (on continue sans reproj) :", e)

    # Calculer union une seule fois
    layer_union = compute_union(gdf_layer)

    # Préparer colonne si elle n'existe pas
    if col not in gdf.columns:
        gdf[col] = pd.Series(dtype='string')  # Définir explicitement comme type string
    else:
        # Convertir la colonne existante en type string si ce n'est pas déjà le cas
        gdf[col] = gdf[col].astype('string')

    # Masque : lignes ayant une géométrie VALIDE (non None) et colonne cible vide
    has_geom = gdf['geometry'].notna()  # True si polygon présent
    # considérer comme "vide" si NaN ou chaîne vide
    is_col_empty = gdf[col].isna() | (gdf[col].astype(str).str.strip() == "")
    mask = has_geom & is_col_empty

    total_to_process = int(mask.sum())
    print(f"Lignes à traiter (géom. présente & colonne vide) : {total_to_process}")

    if total_to_process == 0:
        print("Rien à faire pour cette couche.")
        continue

    # Appliquer l'intersection seulement sur ces lignes
    subset_idx = gdf.loc[mask].index
    results = []
    oui_count = 0
    
    print(f"\nTraitement de {total_to_process} lignes pour la couche '{col}':")
    for idx in subset_idx:
        # Afficher le nom du levé en cours de traitement
        nom_leve = gdf.at[idx, 'Nom_du_levé']
        print(f"\n→ Traitement de '{nom_leve}'")
        
        # Récupérer la géométrie
        geom = gdf.at[idx, 'geometry']
        
        # Si pas d'union possible, on passe
        if layer_union is None:
            val = pd.NA
            print(f"  ⚠️ Impossible de traiter - union non disponible")
        else:
            # Tester intersection
            try:
                inter = geom.intersects(layer_union)
                val = "OUI" if inter else "NON"
                if inter:
                    oui_count += 1
                print(f"  ✓ Résultat pour '{col}': {val}")
            except Exception as e:
                print(f"  ❌ Erreur intersection pour '{nom_leve}' : {e}")
                val = pd.NA
        
        results.append((idx, val))

    # Affecter résultats dans le GeoDataFrame
    for idx, val in results:
        gdf.at[idx, col] = val

    print(f"Traitement terminé pour {col}: {len(results)} lignes évaluées, {oui_count} => OUI")

# === Nettoyage et sauvegarde ===
# On peut conserver la colonne geometry si on veut, sinon la supprimer avant d'écrire le CSV
OUT_CSV = INPUT_CSV  # écrase le même fichier
gdf.drop(columns='geometry').to_csv(OUT_CSV, index=False, encoding='utf-8-sig', sep=SEP)
print("\n✅ Mise à jour terminée. Fichier réécrit :", OUT_CSV)
