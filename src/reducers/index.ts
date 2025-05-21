// src/reducers/index.ts
import { combineReducers } from 'redux';
import { 
  FETCH_ANNOTATIONS, 
  SWITCH_ACTIVE_SELECTION, 
  UPLOAD_ANNOTATIONS,
  NeumeAnnotation,
  AnnotationActionTypes
} from '../types';

// Annotations reducer
function annotationsReducer(
  state: NeumeAnnotation[] | null = null, 
  action: AnnotationActionTypes
): NeumeAnnotation[] | null {
  switch (action.type) {
    case FETCH_ANNOTATIONS:
      return action.payload;
    case UPLOAD_ANNOTATIONS:
      return action.payload;
    default:
      return state;
  }
}

// Active selection reducer
function activeSelectionReducer(
  state: string = '', 
  action: AnnotationActionTypes
): string {
  switch (action.type) {
    case SWITCH_ACTIVE_SELECTION:
      return action.payload;
    default:
      return state;
  }
}

// Combine reducers
const rootReducer = combineReducers({
  annotations: annotationsReducer,
  activeSelection: activeSelectionReducer
});

export default rootReducer;
export type RootState = ReturnType<typeof rootReducer>;