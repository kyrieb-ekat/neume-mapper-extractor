// src/actions/index.ts
import { Dispatch } from 'redux';
import { 
  FETCH_ANNOTATIONS, 
  SWITCH_ACTIVE_SELECTION, 
  UPLOAD_ANNOTATIONS,
  NeumeAnnotation,
  AnnotationActionTypes
} from '../types';
import axios from 'axios';

// Fetch annotations from a JSON file or API
export const fetchAnnotations = () => {
  return async (dispatch: Dispatch<AnnotationActionTypes>) => {
    try {
      // You can replace this URL with your actual API endpoint 
      // or path to your JSON file
      const response = await axios.get<NeumeAnnotation[]>('/sample-annotations.json');
      
      dispatch({
        type: FETCH_ANNOTATIONS,
        payload: response.data
      });
    } catch (error) {
      console.error('Error fetching annotations:', error);
    }
  };
};

// Switch the active neume selection
export const switchActiveSelection = (neumeType: string): AnnotationActionTypes => {
  return {
    type: SWITCH_ACTIVE_SELECTION,
    payload: neumeType
  };
};

// Upload annotations from a file
export const uploadAnnotations = (annotations: NeumeAnnotation[]): AnnotationActionTypes => {
  return {
    type: UPLOAD_ANNOTATIONS,
    payload: annotations
  };
};

// Export annotations to a JSON file
export const exportAnnotations = (annotations: NeumeAnnotation[]): void => {
  const dataStr = JSON.stringify(annotations, null, 2);
  const dataUri = 'data:application/json;charset=utf-8,' + encodeURIComponent(dataStr);
  
  const exportFileDefaultName = 'annotations.json';
  const linkElement = document.createElement('a');
  linkElement.setAttribute('href', dataUri);
  linkElement.setAttribute('download', exportFileDefaultName);
  linkElement.click();
};