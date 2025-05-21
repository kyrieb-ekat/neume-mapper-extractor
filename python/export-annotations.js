// export-annotations.js
// This script can be added to your application to export the annotations

// Add this function to your Application component
exportAnnotations() {
  if (!this.props.annotations) {
    console.error('No annotations to export');
    return;
  }
  
  // Create a data URI for the annotations JSON
  const dataStr = JSON.stringify(this.props.annotations, null, 2);
  const dataUri = 'data:application/json;charset=utf-8,' + encodeURIComponent(dataStr);
  
  // Create a download link and trigger it
  const exportFileDefaultName = 'annotations.json';
  const linkElement = document.createElement('a');
  linkElement.setAttribute('href', dataUri);
  linkElement.setAttribute('download', exportFileDefaultName);
  linkElement.click();
}

// Then add a button to your render method to trigger the export
<button onClick={this.exportAnnotations.bind(this)}>Export Annotations</button> 