import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Paper,
  Grid,
  Button,
  CircularProgress,
  Divider,
  Chip,
  Link
} from '@mui/material';
import MainLayout from '../components/MainLayout';
import { resultService, type ProcessingResult } from '../services/resultService';
import { formatDateRelative } from '../utils/dateUtils';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import DownloadIcon from '@mui/icons-material/Download';
import CalendarTodayIcon from '@mui/icons-material/CalendarToday';
import ArticleIcon from '@mui/icons-material/Article';

const ResultDetailsPage: React.FC = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [result, setResult] = useState<ProcessingResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) {
      setError('ID du résultat manquant');
      return;
    }
    loadResult(id);
  }, [id]);

  const loadResult = async (imageId: string) => {
    try {
      setLoading(true);
      const data = await resultService.getResult(imageId);
      setResult(data);
      setError(null);
    } catch (err) {
      setError('Erreur lors du chargement des détails du résultat');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const getStatusChip = (status: string) => {
    let color: "success" | "warning" | "error" | "default";
    let label: string;

    switch (status) {
      case 'completed':
        color = 'success';
        label = 'Terminé';
        break;
      case 'processing':
        color = 'warning';
        label = 'En cours';
        break;
      case 'failed':
        color = 'error';
        label = 'Échec';
        break;
      default:
        color = 'default';
        label = 'Inconnu';
    }

    return <Chip label={label} color={color} size="small" />;
  };

  if (loading) {
    return (
      <MainLayout title="Détails du Résultat">
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '80vh' }}>
          <CircularProgress />
        </Box>
      </MainLayout>
    );
  }

  if (error || !result) {
    return (
      <MainLayout title="Détails du Résultat">
        <Box sx={{ p: 3 }}>
          <Typography color="error" gutterBottom>{error || 'Résultat non trouvé'}</Typography>
          <Button variant="contained" onClick={() => navigate('/results')}>
            Retour aux résultats
          </Button>
        </Box>
      </MainLayout>
    );
  }

  return (
    <MainLayout title={`Détails - ${result.filename}`}>
      <Box 
        sx={{ 
          bgcolor: '#f8f9fa',
          borderBottom: '1px solid',
          borderColor: 'divider',
          mb: 4
        }}
      >
        <Box sx={{ maxWidth: '1200px', margin: '0 auto', p: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
            <Button 
              startIcon={<ArrowBackIcon />}
              onClick={() => navigate('/results')}
              sx={{ 
                color: 'text.secondary',
                '&:hover': {
                  bgcolor: 'rgba(0,0,0,0.04)'
                }
              }}
            >
              Retour aux résultats
            </Button>
            <Divider orientation="vertical" flexItem />
            {getStatusChip(result.status)}
          </Box>
          
          <Typography variant="h4" component="h1" sx={{ 
            fontWeight: 'bold',
            color: 'text.primary',
            mb: 1
          }}>
            {result.filename}
          </Typography>
          
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, color: 'text.secondary' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <CalendarTodayIcon sx={{ fontSize: 16 }} />
              <Typography variant="body2">
                {formatDateRelative(result.created_at)}
              </Typography>
            </Box>
          </Box>
        </Box>
      </Box>

      <Box sx={{ maxWidth: '1200px', margin: '0 auto', px: 3 }}>

        <Grid container spacing={4}>
          {/* Colonne de gauche - Image et métadonnées */}
          <Grid item xs={12} md={8}>
            <Paper sx={{ p: 3, mb: 3 }} elevation={1}>
              <Typography variant="h5" gutterBottom sx={{ fontWeight: 'bold' }}>
                {result.filename}
              </Typography>
              
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <CalendarTodayIcon sx={{ fontSize: 16, color: 'text.secondary' }} />
                  <Typography variant="body2" color="text.secondary">
                    {formatDateRelative(result.created_at)}
                  </Typography>
                </Box>
              </Box>

              {/* Image du levé */}
              <Paper 
                elevation={2}
                sx={{ 
                  width: '100%', 
                  mb: 3,
                  p: 2,
                  backgroundColor: '#f8f9fa',
                  borderRadius: 2,
                  overflow: 'hidden'
                }}
              >
                <Box
                  sx={{
                    position: 'relative',
                    width: '100%',
                    pt: '70%', // Aspect ratio 10:7
                    borderRadius: 1,
                    overflow: 'hidden',
                    boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                    backgroundColor: '#fff'
                  }}
                >
                  <Box
                    component="img"
                    src={result.file_url}
                    alt={result.filename}
                    sx={{
                      position: 'absolute',
                      top: 0,
                      left: 0,
                      width: '100%',
                      height: '100%',
                      objectFit: 'contain',
                      transition: 'transform 0.3s ease',
                      '&:hover': {
                        transform: 'scale(1.02)'
                      }
                    }}
                  />
                </Box>
              </Paper>

              {/* Boutons d'action */}
              <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', justifyContent: 'center' }}>
                <Button
                  variant="contained"
                  startIcon={<DownloadIcon />}
                  href={result.file_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  sx={{
                    bgcolor: 'primary.main',
                    color: 'white',
                    '&:hover': {
                      bgcolor: 'primary.dark'
                    },
                    minWidth: '200px'
                  }}
                >
                  Télécharger l'image
                </Button>
                {result.summary_pdf && (
                  <Button
                    variant="contained"
                    startIcon={<ArticleIcon />}
                    href={result.summary_pdf}
                    target="_blank"
                    rel="noopener noreferrer"
                    sx={{
                      bgcolor: '#2e7d32',
                      color: 'white',
                      '&:hover': {
                        bgcolor: '#1b5e20'
                      },
                      minWidth: '200px'
                    }}
                  >
                    Voir le résumé PDF
                  </Button>
                )}
              </Box>
            </Paper>
          </Grid>

          {/* Colonne de droite - Résultats de l'analyse */}
          <Grid item xs={12} md={4}>
            <Paper 
              sx={{ 
                p: 3,
                borderRadius: 2,
                bgcolor: '#fff',
                height: '100%'
              }} 
              elevation={2}
            >
              <Typography 
                variant="h6" 
                gutterBottom 
                sx={{ 
                  fontWeight: 'bold', 
                  mb: 3,
                  color: 'primary.main',
                  borderBottom: '2px solid',
                  borderColor: 'primary.main',
                  pb: 1
                }}
              >
                Résultats de l'analyse
              </Typography>

              {result.zones_result && Object.entries(result.zones_result).map(([key, value]) => {
                // Exclure les champs techniques
                if (key === 'original_pdf_url' || key === 'original_pdf_name') return null;
                
                // Formater la valeur pour l'affichage
                let displayValue = value;
                if (typeof value === 'object') {
                  try {
                    // Si c'est un objet, on le formate proprement
                    displayValue = (
                      <Box 
                        component="pre"
                        sx={{
                          bgcolor: '#f8f9fa',
                          p: 1.5,
                          borderRadius: 1,
                          overflow: 'auto',
                          fontSize: '0.875rem',
                          fontFamily: 'monospace',
                          maxHeight: '200px'
                        }}
                      >
                        {JSON.stringify(value, null, 2)}
                      </Box>
                    );
                  } catch (e) {
                    displayValue = String(value);
                  }
                }

                return (
                  <Box 
                    key={key} 
                    sx={{ 
                      mb: 3,
                      '&:last-child .MuiDivider-root': {
                        display: 'none'
                      }
                    }}
                  >
                    <Typography 
                      variant="subtitle2" 
                      sx={{ 
                        color: 'text.primary',
                        mb: 1,
                        fontWeight: 600,
                        display: 'flex',
                        alignItems: 'center',
                        gap: 1
                      }}
                    >
                      <Box 
                        component="span"
                        sx={{ 
                          width: 8,
                          height: 8,
                          borderRadius: '50%',
                          bgcolor: 'primary.main',
                          display: 'inline-block'
                        }}
                      />
                      {key.charAt(0).toUpperCase() + key.slice(1).replace(/_/g, ' ')}
                    </Typography>
                    <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                      {displayValue}
                    </Typography>
                    <Divider sx={{ mt: 2 }} />
                  </Box>
                );
              })}

              {/* La liste des boutons d'action a été déplacée vers la colonne de gauche */}
            </Paper>
          </Grid>
        </Grid>
      </Box>
    </MainLayout>
  );
};

export default ResultDetailsPage;