import geopandas as gpd
import folium
from shapely.geometry import Polygon
import json


SCR_SOURCE = 'EPSG:32231' 

# Définition des couleurs 
LAYER_COLORS = {
    "aif": "#6B8E23",             # Vert Olive Mât (Administratif)
    "air_proteges": "#3CB371",    # Vert Mère (Protection Environnementale)
    "dpl": "#1E90FF",
    "dpm": "#00CED1",
    "enregistrement individuel": "#FFD700",
    "litige": "#FF0000",          # Rouge (Alerte)
    "parcelles": "#8B4513",
    "restriction": "#FF8C00",     # Orange (Avertissement)
    "tf_demembres": "#9932CC",
    "tf_en_cours": "#00FF7F",
    "tf_etat": "#4169E1",
    "titre_reconstitue": "#DC143C",
    "zone_inondable": "#87CEFA"   # Bleu Ciel (Risque Naturel)
}


def convert_datetime_columns_to_str(gdf):
    datetime_cols = gdf.select_dtypes(include=['datetime64[ns]', 'datetime64[ns, UTC]']).columns
    for col in datetime_cols:
        gdf[col] = gdf[col].astype(str)
    return gdf

def generate_visual_map(raw_coords: list, andf_layers: dict, radius_meters: int = 5000) -> str:
    """
    Prend les coordonnées brutes, effectue la projection et génère le HTML de la carte Folium.
    
    :param raw_coords: Liste des coordonnées du relevé (format [{"x": ..., "y": ...}, ...])
    :param andf_layers: Dictionnaire des GeoDataFrames des couches de données (chargées une seule fois au démarrage du serveur)
    :param radius_meters: Rayon de filtrage des couches autour du terrain
    :return: Chaîne de caractères contenant le code HTML complet de la carte Folium.
    """
    
    # 1. Création et Transformation du Polygone du Terrain (Logique des Cellules 49, 50)
    points = [(c["x"], c["y"]) for c in raw_coords]
    parcel = Polygon(points)
    
    parcel_gdf = gpd.GeoSeries([parcel], crs=SCR_SOURCE)
    parcel_wgs84 = parcel_gdf.to_crs(epsg=4326).iloc[0]

    center_point_wgs84 = parcel_wgs84.centroid
    center_lat, center_lon = center_point_wgs84.y, center_point_wgs84.x
    points_wgs84_folium = [(lat, lon) for lon, lat in parcel_wgs84.exterior.coords]

    # 2. Initialisation de la Carte 
    m = folium.Map(location=[center_lat, center_lon], zoom_start=18, prefer_canvas=True) 

    # 3. Ajout des Couches 
    center_point_unprojected = parcel.centroid # On utilise le centroïde non projeté pour le filtre de distance
    
    for layer_name, gdf in andf_layers.items():
        if gdf.crs is None:
            gdf.set_crs(SCR_SOURCE, inplace=True) 

        filtered_gdf = gdf[gdf.geometry.distance(center_point_unprojected) <= radius_meters]

        if filtered_gdf.empty:
            continue
            
        # Transformation en WGS 84 pour l'affichage
        filtered_gdf_wgs84 = filtered_gdf.to_crs(epsg=4326)
        
        filtered_gdf_str_converted = convert_datetime_columns_to_str(filtered_gdf_wgs84)
        geojson_str = filtered_gdf_str_converted.to_json()
        geojson_data = json.loads(geojson_str)

        color = LAYER_COLORS.get(layer_name, "gray")

        folium.GeoJson(
            geojson_data,
            name=layer_name,
            style_function=lambda feature, col=color: {
                'fillColor': col, 'color': col, 'weight': 2, 'fillOpacity': 0.4
            }
        ).add_to(m)

    # 4. Ajout du Polygone du Terrain
    folium.Polygon(
        locations=points_wgs84_folium,
        color='blue', weight=3, fill=True, fill_opacity=0.2, popup='Terrain utilisateur'
    ).add_to(m)
    
    folium.LayerControl().add_to(m)

    # Retourne le HTML complet pour affichage dans la page web
    return m._repr_html_()