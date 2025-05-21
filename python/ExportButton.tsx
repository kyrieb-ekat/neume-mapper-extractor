// src/components/ExportButton.tsx
import React, { useState } from 'react';
import { Button, Modal, Spinner, Alert } from 'react-bootstrap';

interface ExportButtonProps {
  neumeType: string;
  count: number;
}

const ExportButton: React.FC<ExportButtonProps> = ({ neumeType, count }) => {
  const [showModal, setShowModal] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [exportComplete, setExportComplete] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleExport = () => {
    setShowModal(true);
  };

  const handleConfirm = () => {
    setExporting(true);
    setError(null);
    
    // In a real implementation, this would call an API endpoint to trigger the Python script
    // For now, we'll just simulate the export process
    setTimeout(() => {
      // Simulate successful export
      setExporting(false);
      setExportComplete(true);
    }, 2000);
  };

  const handleClose = () => {
    setShowModal(false);
    setExporting(false);
    setExportComplete(false);
    setError(null);
  };

  return (
    <>
      <Button 
        variant="outline-primary" 
        size="sm" 
        onClick={handleExport}
      >
        Export {count} {neumeType} Images
      </Button>

      <Modal show={showModal} onHide={handleClose}>
        <Modal.Header closeButton>
          <Modal.Title>Export Neume Images</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {!exporting && !exportComplete && !error && (
            <div>
              <p>This will export {count} individual images of the <strong>{neumeType}</strong> neume type.</p>
              <p>The images will be saved to the <code>public/exported_neumes/{neumeType.replace(/\s+/g, '_')}</code> directory.</p>
              <p>A metadata file will also be created with information about each neume.</p>
            </div>
          )}
          
          {exporting && (
            <div className="text-center my-4">
              <Spinner animation="border" role="status">
                <span className="visually-hidden">Exporting...</span>
              </Spinner>
              <p className="mt-2">Exporting {count} neume images...</p>
            </div>
          )}
          
          {exportComplete && (
            <Alert variant="success">
              <Alert.Heading>Export Complete!</Alert.Heading>
              <p>
                Successfully exported {count} images of {neumeType} neumes.
              </p>
              <p>
                The images are now available in the <code>public/exported_neumes/{neumeType.replace(/\s+/g, '_')}</code> directory.
              </p>
              <hr />
              <p className="mb-0">
                To use these images in your project, run the export script manually:
              </p>
              <pre className="mt-2">
                <code>
                  cd python{'\n'}
                  python export_neumes.py --filter-type "{neumeType}"
                </code>
              </pre>
            </Alert>
          )}
          
          {error && (
            <Alert variant="danger">
              <Alert.Heading>Export Failed</Alert.Heading>
              <p>{error}</p>
            </Alert>
          )}
        </Modal.Body>
        <Modal.Footer>
          {!exporting && !exportComplete && (
            <Button variant="primary" onClick={handleConfirm}>
              Export
            </Button>
          )}
          <Button variant="secondary" onClick={handleClose}>
            {exportComplete ? 'Close' : 'Cancel'}
          </Button>
        </Modal.Footer>
      </Modal>
    </>
  );
};

export default ExportButton;