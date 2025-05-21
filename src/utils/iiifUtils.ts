// src/utils/iiifUtils.ts
import { IIIFImageInfo } from '../types';

/**
 * Parse an IIIF URL into its components
 * @param url The IIIF URL to parse
 * @returns Parsed IIIF image information or null if parsing fails
 */
export function parseIiifUrl(url: string): IIIFImageInfo | null {
  try {
    const baseUrl = url.replace(/\/[\d]+,[\d]+,[\d]+,[\d]+\/64,\/0\/default.jpg/, "");
    const dimsMatch = url.match(/[\d]+,[\d]+,[\d]+,[\d]+/);
    
    if (!dimsMatch) {
      return null;
    }
    
    const dims = dimsMatch[0].split(",");
    const urlParts = url.split('/');
    
    return {
      baseUrl,
      x: parseInt(dims[0], 10),
      y: parseInt(dims[1], 10),
      width: parseInt(dims[2], 10),
      height: parseInt(dims[3], 10),
      pageId: urlParts.length > 6 ? urlParts[6] : "unknown"
    };
  } catch (error) {
    console.error("Error parsing IIIF URL:", error);
    return null;
  }
}

/**
 * Create a direct region URL for an IIIF image
 * @param info The parsed IIIF image information
 * @param size Size parameter for the IIIF request (default: 'full')
 * @returns Full URL to request just the specified region
 */
export function createRegionUrl(info: IIIFImageInfo, size: string = 'full'): string {
  const region = `${info.x},${info.y},${info.width},${info.height}`;
  return `${info.baseUrl}/${region}/${size}/0/default.jpg`;
}

/**
 * Create a URL for viewing the image in a IIIF viewer
 * @param info The parsed IIIF image information
 * @returns URL to open the image in the Diva.js IIIF viewer
 */
export function createViewerUrl(info: IIIFImageInfo): string {
  const imgUri = encodeURI(info.baseUrl);
  return `http://ddmal.github.io/diva.js/try/iiif-highlight-pages/#v=d&z=5&n=5&i=${imgUri}&y=${info.y}&x=${info.x}`;
}