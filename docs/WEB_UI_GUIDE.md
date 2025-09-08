# Web UI Guide

## Overview

The Web UI provides an intuitive interface for processing address data and extracting apartment access codes. It offers real-time processing, configuration management, and result visualization.

## Getting Started

### Environment Setup

1. **Configure environment variables**
   ```bash
   cp config/.env.example config/.env
   # Edit config/.env to add your API keys
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

### Starting the Service

**Method 1: Direct Python execution**
```bash
cd ui
python app.py
```

**Method 2: Flask command**
```bash
flask --app ui/app.py run --port 5001
```

**Method 3: Using startup script**
```bash
./scripts/start_web.sh
```

### Accessing the Interface

Open your browser and navigate to: **http://localhost:5001**

## Interface Features

### Main Dashboard

#### File Upload Section
- **Drag & Drop**: Simply drag CSV files into the upload area
- **Browse Files**: Click to select files from your computer
- **Format Validation**: Automatic validation of file format and structure
- **Preview**: View file contents before processing

#### Configuration Panel
- **API Settings**: Configure Placekey API credentials
- **Processing Options**: Adjust concurrency and timeout settings
- **Column Mapping**: Customize CSV column mappings
- **Output Format**: Choose between CSV and JSON output formats

#### Processing Controls
- **Start Processing**: Begin batch processing with current settings
- **Progress Tracking**: Real-time progress bar and status updates
- **Cancel Operation**: Stop processing if needed
- **Download Templates**: Get sample input file templates

#### Results Display
- **Processing Summary**: Overview of results and statistics
- **Data Preview**: View processed data in tabular format
- **Download Results**: Export processed data in various formats
- **Error Reports**: View detailed error logs and failed records

## Usage Steps

### Step 1: Upload Data
1. Click the upload area or drag files directly
2. Select your CSV file containing address data
3. Wait for file validation and preview
4. Review the detected columns and data structure

### Step 2: Configure Settings
1. **API Configuration**:
   - Enter your Placekey API key (optional)
   - Set API timeout and retry settings

2. **Processing Options**:
   - Adjust worker thread count (1-10)
   - Enable/disable apartment aggregation
   - Set confidence thresholds

3. **Column Mapping**:
   - Map your CSV columns to required fields
   - Preview mapping results
   - Save custom mappings for future use

### Step 3: Process Data
1. Click "Start Processing" button
2. Monitor progress through the progress bar
3. View real-time processing statistics
4. Wait for completion notification

### Step 4: Review Results
1. **Summary Statistics**:
   - Total records processed
   - Apartment detection rate
   - Confidence score distribution
   - Processing time and performance metrics

2. **Data Preview**:
   - Browse processed records
   - Filter by confidence levels
   - Sort by various criteria
   - Highlight detected apartments

3. **Download Results**:
   - Choose output format (CSV/JSON)
   - Download complete results
   - Export error reports
   - Save processing logs

## Advanced Features

### Batch Processing
- **Multiple Files**: Process multiple CSV files simultaneously
- **Queue Management**: View and manage processing queue
- **Scheduled Processing**: Set up automated processing schedules

### Data Visualization
- **Confidence Distribution**: Charts showing detection confidence levels
- **Geographic Mapping**: Map view of processed addresses (if coordinates available)
- **Processing Statistics**: Performance metrics and trends

### Export Options
- **CSV Export**: Standard comma-separated values format
- **JSON Export**: Structured JSON format for API integration
- **Excel Export**: Microsoft Excel compatible format
- **Report Generation**: Comprehensive processing reports

## Configuration Management

### API Settings
- **Placekey API**: Configure API key and endpoint settings
- **Rate Limiting**: Set request rate limits to avoid quota issues
- **Timeout Settings**: Adjust timeout values for API requests

### Processing Settings
- **Concurrency**: Control number of parallel processing threads
- **Memory Management**: Set memory limits for large datasets
- **Error Handling**: Configure error tolerance and retry logic

### UI Preferences
- **Theme Settings**: Choose between light and dark themes
- **Language**: Select interface language (English/Chinese)
- **Display Options**: Customize table views and chart preferences

## Troubleshooting

### Common Issues

1. **Server Won't Start**
   - Check if port 5001 is already in use
   - Verify Python dependencies are installed
   - Review error logs in the console

2. **File Upload Fails**
   - Ensure file is in CSV format
   - Check file size limits (max 100MB)
   - Verify file encoding (UTF-8 recommended)

3. **Processing Errors**
   - Validate input data format
   - Check API key configuration
   - Review network connectivity

4. **Performance Issues**
   - Reduce worker thread count
   - Process smaller batches
   - Check system memory usage

### Debug Mode

Enable debug mode by setting `FLASK_DEBUG=1` in your environment:
```bash
export FLASK_DEBUG=1
flask --app ui/app.py run --port 5001
```

### Log Files

Check application logs for detailed error information:
- **Application Logs**: `logs/app.log`
- **Processing Logs**: `logs/processing.log`
- **Error Logs**: `logs/error.log`

## Browser Compatibility

### Supported Browsers
- **Chrome**: Version 80+
- **Firefox**: Version 75+
- **Safari**: Version 13+
- **Edge**: Version 80+

### Recommended Settings
- Enable JavaScript
- Allow file uploads
- Disable popup blockers for the application domain

## Security Considerations

### Data Privacy
- All processing is done locally on your server
- No data is stored permanently unless explicitly saved
- API keys are encrypted in transit

### Access Control
- Consider implementing authentication for production use
- Use HTTPS in production environments
- Regularly update dependencies for security patches

## Performance Tips

### Optimal Settings
- Use 2-4 worker threads for most systems
- Process files in batches of 1000-5000 records
- Enable API caching for repeated addresses

### System Requirements
- **RAM**: Minimum 4GB, recommended 8GB+
- **CPU**: Multi-core processor recommended
- **Storage**: Sufficient space for input/output files
- **Network**: Stable internet connection for API access