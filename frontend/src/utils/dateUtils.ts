import { formatDistanceToNow } from 'date-fns';
import { fr } from 'date-fns/locale';

export const formatDateRelative = (dateString: string | undefined | null): string => {
  if (!dateString) return 'Date inconnue';
  
  try {
    const date = new Date(dateString);
    // Vérifier si la date est valide
    if (isNaN(date.getTime())) {
      return 'Date invalide';
    }
    return formatDistanceToNow(date, { addSuffix: true, locale: fr });
  } catch (error) {
    console.error('Erreur de formatage de date:', error);
    return 'Date invalide';
  }
};