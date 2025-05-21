// src/components/SimpleReferenceViewer.tsx
import React, { useState } from 'react';
import { Card, Button, Alert, Container, Row, Col, Spinner } from 'react-bootstrap';

interface SimpleReferenceViewerProps {
  neumeType: string;
}

const SimpleReferenceViewer: React.FC<SimpleReferenceViewerProps> = ({ neumeType }) => {
  const [showOriginal, setShowOriginal] = useState<boolean>(true);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  
  // Try different overlay file patterns (in order of preference)
  const overlayOptions = [
    `/reference_images/SG_390-007_overlay_auto_web.jpg`,
    `/reference_images/SG_390-007_overlay_auto.jpg`,
    `/reference_images/SG_390-007_overlay_fixed.jpg`,
    `/reference_images/SG_390-007_overlay.jpg`,
    `/reference_images/SG_390-007_overlay_${neumeType.replace(/\s+/g, '_')}.jpg`
  ];
  
  // Hardcoded path to your specific images
  const originalImagePath = '/reference_images/SG_390-007.jpg';
  
  const toggleView = () => {
    setShowOriginal(!showOriginal);
    setLoading(true);
    setError(null);
  };
  
  const handleImageLoad = () => {
    setLoading(false);
  };
  
  const handleImageError = (e: React.SyntheticEvent<HTMLImageElement>) => {
    console.error("Image failed to load:", e.currentTarget.src);
    
    // Get the current src
    const currentSrc = e.currentTarget.src.split('?')[0];
    
    // Find current index in overlayOptions
    const currentIndex = overlayOptions.findIndex(path => currentSrc.endsWith(path));
    
    if (currentIndex >= 0 && currentIndex < overlayOptions.length - 1) {
      // Try the next option
      const nextOption = overlayOptions[currentIndex + 1];
      console.log(`Trying next overlay option: ${nextOption}`);
      e.currentTarget.src = `${nextOption}?t=${Date.now()}`;
    } else {
      // We've tried all options
      setLoading(false);
      setError("Could not load any overlay images");
    }
  };
  
  return (
    <Card>
      <Card.Header className="d-flex justify-content-between align-items-center">
        <h5 className="mb-0">Reference Image for {neumeType}</h5>
        <Button variant="outline-primary" size="sm" onClick={toggleView}>
          {showOriginal ? "Show Overlay" : "Show Original"}
        </Button>
      </Card.Header>
      <Card.Body>
        <div className="text-center mb-3">
          <p>Viewing {showOriginal ? "Original Image" : "Overlay with Neumes Highlighted"}</p>
        </div>
        
        <Container>
          <Row className="justify-content-center">
            <Col xs={12} className="text-center">
              {loading && (
                <div className="text-center my-3">
                  <Spinner animation="border" role="status">
                    <span className="visually-hidden">Loading...</span>
                  </Spinner>
                </div>
              )}
              
              {error && !showOriginal && (
                <Alert variant="warning">
                  {error}. Please run the overlay generation script.
                </Alert>
              )}
              
              <div style={{ maxHeight: '600px', overflow: 'auto', border: '1px solid #ddd', borderRadius: '4px' }}>
                {/* Add time parameter to avoid browser caching */}
                <img 
                  src={showOriginal ? 
                    `${originalImagePath}?t=${Date.now()}` : 
                    `${overlayOptions[0]}?t=${Date.now()}`}
                  alt={showOriginal ? "Original manuscript page" : "Overlay with neumes highlighted"} 
                  style={{ 
                    maxWidth: '100%', 
                    display: (loading && !showOriginal) ? 'none' : 'block'
                  }}
                  onLoad={handleImageLoad}
                  onError={showOriginal ? undefined : handleImageError}
                />
              </div>
            </Col>
          </Row>
        </Container>
        
        <div className="d-flex justify-content-center mt-3">
          <Button 
            variant="outline-secondary" 
            href={showOriginal ? originalImagePath : overlayOptions[0]} 
            target="_blank"
            className="me-2"
          >
            View Full Size
          </Button>
          
          {!showOriginal && (
            <Button 
              variant="outline-primary"
              onClick={() => window.location.href = '/test-images.html'}
            >
              Test All Images
            </Button>
          )}
        </div>
      </Card.Body>
    </Card>
  );
};

export default SimpleReferenceViewer;