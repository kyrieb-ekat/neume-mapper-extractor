// src/services/annotationService.ts
import axios from 'axios';
import { NeumeAnnotation } from '../types';

/**
 * Service for handling annotations data
 */
export class AnnotationService {
  /**
   * Fetch annotations from a JSON file or API
   * @param url URL to fetch annotations from
   * @returns Promise with annotations data
   */
  static async fetchAnnotations(url: string = '/sample-annotations.json'): Promise<NeumeAnnotation[]> {
    try {
      const response = await axios.get<NeumeAnnotation[]>(url);
      return response.data;
    } catch (error) {
      console.error('Error fetching annotations:', error);
      throw error;
    }
  }

  /**
   * Export annotations to a JSON file
   * @param annotations Annotations to export
   * @param filename Name of the file to download
   */
  static exportAnnotations(annotations: NeumeAnnotation[], filename: string = 'annotations.json'): void {
    const dataStr = JSON.stringify(annotations, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,' + encodeURIComponent(dataStr);
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', filename);
    linkElement.click();
  }

  /**
   * Parse annotations from a JSON string
   * @param jsonString JSON string containing annotations
   * @returns Parsed annotations
   */
  static parseAnnotations(jsonString: string): NeumeAnnotation[] {
    try {
      return JSON.parse(jsonString) as NeumeAnnotation[];
    } catch (error) {
      console.error('Error parsing annotations:', error);
      throw new Error('Invalid JSON format');
    }
  }

  /**
   * Validate annotations data
   * @param annotations Annotations to validate
   * @returns True if valid, false otherwise
   */
  static validateAnnotations(annotations: any): boolean {
    if (!Array.isArray(annotations)) {
      return false;
    }
    
    return annotations.every(item => 
      typeof item === 'object' && 
      item !== null &&
      typeof item.type === 'string' && 
      Array.isArray(item.urls)
    );
  }
}

export default AnnotationService;