// src/components/ImageComponent.tsx
import React from 'react';
import { Card, ListGroup } from 'react-bootstrap';
import { parseIiifUrl, createViewerUrl } from '../utils/iiifUtils';

interface ImageComponentProps {
  url: string;
}

const ImageComponent: React.FC<ImageComponentProps> = ({ url }) => {
  // Parse the IIIF URL using our utility function
  const imageInfo = parseIiifUrl(url);
  
  // If parsing fails, show an error card
  if (!imageInfo) {
    return (
      <Card className="h-100">
        <Card.Body>
          <Card.Text className="text-danger">Invalid IIIF URL format</Card.Text>
        </Card.Body>
      </Card>
    );
  }
  
  // Create viewer URL
  const viewerUrl = createViewerUrl(imageInfo);

  return (
    <Card className="h-100">
      <a href={viewerUrl} target="_blank" rel="noopener noreferrer" className="text-decoration-none">
        <Card.Img variant="top" src={url} alt={`Neume at ${imageInfo.x},${imageInfo.y}`} />
      </a>
      <Card.Body className="p-2">
        <ListGroup variant="flush" className="small">
          <ListGroup.Item className="py-1 px-2">
            <strong>Page:</strong> {imageInfo.pageId}
          </ListGroup.Item>
          <ListGroup.Item className="py-1 px-2">
            <strong>Position:</strong> {imageInfo.x},{imageInfo.y}
          </ListGroup.Item>
          <ListGroup.Item className="py-1 px-2">
            <strong>Size:</strong> {imageInfo.width}×{imageInfo.height}
          </ListGroup.Item>
        </ListGroup>
      </Card.Body>
    </Card>
  );
};

export default ImageComponent;