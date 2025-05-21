// src/components/NeumeViewer.tsx
import React, { useState, ChangeEvent } from 'react';
import { connect } from 'react-redux';
import { 
  Card, Button, Form, InputGroup, 
  Row, Col, Alert, Container, Tabs, Tab
} from 'react-bootstrap';
import { switchActiveSelection, exportAnnotations } from '../actions';
import ImageComponent from './ImageComponent';
import ReferenceViewer from './ReferenceViewer';
import { NeumeAnnotation, RootState } from '../types';
import ExportButton from './ExportButton';

interface NeumeViewerProps {
  annotations: NeumeAnnotation[] | null;
  activeSelection: string;
  switchActiveSelection: (neumeType: string) => void;
  uploadAnnotations: (annotations: NeumeAnnotation[]) => void;
}

const NeumeViewer: React.FC<NeumeViewerProps> = (props) => {
  const { annotations, activeSelection, switchActiveSelection, uploadAnnotations } = props;
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [sortOption, setSortOption] = useState<'type' | 'count'>('type');
  const [activeTab, setActiveTab] = useState<string>('images');

  // Handle export annotations
  const handleExport = (): void => {
    if (annotations) {
      exportAnnotations(annotations);
    }
  };

  // Allow file upload of annotations
  const handleFileUpload = (event: ChangeEvent<HTMLInputElement>): void => {
    const files = event.target.files;
    if (!files || files.length === 0) return;
    
    const file = files[0];
    const reader = new FileReader();
    
    reader.onload = (e: ProgressEvent<FileReader>) => {
      try {
        if (!e.target?.result) return;
        const parsedData = JSON.parse(e.target.result as string) as NeumeAnnotation[];
        uploadAnnotations(parsedData);
      } catch (error) {
        console.error('Error parsing JSON file:', error);
        alert('Invalid JSON file');
      }
    };
    
    reader.readAsText(file);
  };

  // If no annotations yet, show loading or upload option
  if (!annotations) {
    return (
      <Card>
        <Card.Body className="text-center py-5">
          <Card.Title>Neume Viewer</Card.Title>
          <Card.Text className="mb-4">
            No annotations loaded. Please upload a JSON file or wait for data to load.
          </Card.Text>
          <Form.Group controlId="formFile" className="mb-3">
            <Form.Control 
              type="file" 
              accept=".json" 
              onChange={handleFileUpload}
            />
          </Form.Group>
        </Card.Body>
      </Card>
    );
  }

  // Filter annotations based on search term
  const filteredAnnotations = annotations.filter(annot => 
    annot.type.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Sort annotations
  const sortedAnnotations = [...filteredAnnotations].sort((a, b) => {
    if (sortOption === 'type') {
      return a.type.localeCompare(b.type);
    } else {
      return b.urls.length - a.urls.length;
    }
  });

  // Find the selected annotation
  const selectedAnnotation = annotations.find(
    annot => annot.type === activeSelection
  );

  return (
          <Card>
      <Card.Header>
        <Container fluid>
          <Row className="align-items-center mb-2">
            <Col xs={12} md={4}>
              <h5 className="mb-md-0 mb-2">Neume Viewer</h5>
            </Col>
            <Col xs={12} md={8} className="d-flex flex-wrap gap-2 justify-content-md-end">
              <Button 
                variant="primary" 
                size="sm" 
                onClick={handleExport}
                className="me-2 flex-shrink-0"
              >
                Export Annotations
              </Button>
              
              <Form.Control
                type="file"
                size="sm"
                accept=".json"
                onChange={handleFileUpload}
                style={{ width: 'auto', maxWidth: '220px' }}
                className="flex-shrink-0"
              />
            </Col>
          </Row>
          
          <Row>
            <Col xs={12}>
              <InputGroup size="sm">
                <Form.Control
                  placeholder="Search neumes..."
                  value={searchTerm}
                  onChange={(e: ChangeEvent<HTMLInputElement>) => setSearchTerm(e.target.value)}
                />
                <Form.Select 
                  value={sortOption} 
                  onChange={(e: ChangeEvent<HTMLSelectElement>) => 
                    setSortOption(e.target.value as 'type' | 'count')}
                  style={{ maxWidth: '150px' }}
                >
                  <option value="type">Sort by Type</option>
                  <option value="count">Sort by Count</option>
                </Form.Select>
              </InputGroup>
            </Col>
          </Row>
        </Container>
      </Card.Header>
      
      <Card.Body>
        <Form.Group className="mb-4">
          <Form.Label>Select Neume Type</Form.Label>
          <Form.Select 
            onChange={(e: ChangeEvent<HTMLSelectElement>) => switchActiveSelection(e.target.value)}
          >
            <option value="">Select a neume type</option>
            {sortedAnnotations.map((annot, idx) => (
              <option key={idx} value={annot.type}>
                {annot.type} ({annot.urls.length})
              </option>
            ))}
          </Form.Select>
        </Form.Group>
        
        {selectedAnnotation ? (
          <div className="selected-neume">
            <Alert variant="info">
              Viewing: {selectedAnnotation.type} ({selectedAnnotation.urls.length} images)
              <Alert variant="info" className="d-flex justify-content-between align-items-center">
              <div>
                Viewing: {selectedAnnotation.type} ({selectedAnnotation.urls.length} images)
              </div>
              <ExportButton 
                neumeType={selectedAnnotation.type} 
                count={selectedAnnotation.urls.length} 
              />
            </Alert>  
            </Alert>
            
            <Tabs
              activeKey={activeTab}
              onSelect={(k) => setActiveTab(k || 'images')}
              className="mb-3"
            >
              <Tab eventKey="images" title="Individual Images">
                <Row xs={1} sm={2} md={3} lg={4} className="g-4">
                  {selectedAnnotation.urls.map((url, idx) => (
                    <Col key={idx}>
                      <ImageComponent url={url} />
                    </Col>
                  ))}
                </Row>
              </Tab>
              <Tab eventKey="reference" title="Reference Images">
                <ReferenceViewer 
                  neumeType={selectedAnnotation.type} 
                  urls={selectedAnnotation.urls} 
                />
              </Tab>
            </Tabs>
          </div>
        ) : (
          <Alert variant="secondary">
            Select a neume type from the dropdown to view images
          </Alert>
        )}
      </Card.Body>
    </Card>
  );
};

const mapStateToProps = (state: RootState) => {
  return {
    annotations: state.annotations,
    activeSelection: state.activeSelection
  };
};

export default connect(
  mapStateToProps, 
  { switchActiveSelection }
)(NeumeViewer);