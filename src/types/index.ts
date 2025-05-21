// src/types/index.ts

// Define the structure of a neume annotation
export interface NeumeAnnotation {
  type: string;
  urls: string[];
  // You can add more fields here if needed
  metadata?: {
    source?: string;
    description?: string;
    dateAdded?: string;
  };
}

// Define the Redux state structure
export interface RootState {
  annotations: NeumeAnnotation[] | null;
  activeSelection: string;
}

// Action type constants
export const FETCH_ANNOTATIONS = 'FETCH_ANNOTATIONS';
export const SWITCH_ACTIVE_SELECTION = 'SWITCH_ACTIVE_SELECTION';
export const UPLOAD_ANNOTATIONS = 'UPLOAD_ANNOTATIONS';

// Action interfaces
export interface FetchAnnotationsAction {
  type: typeof FETCH_ANNOTATIONS;
  payload: NeumeAnnotation[];
}

export interface SwitchActiveSelectionAction {
  type: typeof SWITCH_ACTIVE_SELECTION;
  payload: string;
}

export interface UploadAnnotationsAction {
  type: typeof UPLOAD_ANNOTATIONS;
  payload: NeumeAnnotation[];
}

// Union type for all possible action types
export type AnnotationActionTypes = 
  | FetchAnnotationsAction 
  | SwitchActiveSelectionAction
  | UploadAnnotationsAction;

// Type for a IIIF URL parsed components
export interface IIIFImageInfo {
  baseUrl: string;
  x: number;
  y: number;
  width: number;
  height: number;
  pageId: string;
}