# Quick Start Guide

## Overview

This guide helps you quickly get started with the Apartment Access Code Extraction Tool. The tool intelligently identifies apartment addresses and extracts access codes from address strings.

## Environment Setup

### System Requirements
- Python 3.8+
- pip package manager
- Placekey API key (optional, for enhanced functionality)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Apartment-accesscode
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure API keys**
   ```bash
   cp config/.env.example config/.env
   # Edit config/.env and add your Placekey API key
   ```

## Basic Usage

### Command Line Processing

1. **Prepare input data**
   - Place CSV files in `data/input/` directory
   - Ensure files follow the standard format (see examples)

2. **Run batch processing**
   ```bash
   python main.py batch -i data/input/your_file.csv -o data/output/result.csv
   ```

3. **Enable apartment aggregation**
   ```bash
   python main.py batch -i data/input/your_file.csv -o data/output/result.csv --aggregate
   ```

4. **Adjust concurrency**
   ```bash
   python main.py batch -i data/input/your_file.csv -o data/output/result.csv --workers 5
   ```

### Web Interface

1. **Start the web server**
   ```bash
   python ui/app.py
   # or
   flask --app ui/app.py run --port 5001
   ```

2. **Access the interface**
   - Open browser and navigate to: http://localhost:5001
   - Upload CSV files through the web interface
   - Configure API settings
   - Download processing templates
   - View results in real-time

## Processing Standard Format

**Input file path**: `data/input/your_file.csv`
**Output file path**: `data/output/processed_your_file.csv`

### Required Columns
- `street_address`: Full street address
- `city`: City name
- `region`: State/Province code
- `postal_code`: ZIP/Postal code
- `iso_country_code`: Country code (e.g., "US")

### Output Columns
- All original columns
- `has_apartment`: Boolean indicating apartment detection
- `apartment_type`: Type of apartment (apt, unit, suite, etc.)
- `access_code`: Extracted access code
- `confidence`: Detection confidence score
- `placekey`: Placekey identifier (if API enabled)

## Next Steps

- Review [Solution Guide](SOLUTION_GUIDE.md) for detailed technical information
- Check [Web UI Guide](WEB_UI_GUIDE.md) for web interface usage
- See [User Guide](../CN_Introduction/USER_GUIDE.md) for comprehensive usage instructions (Chinese)

## Support

For technical support or questions, please refer to the documentation or create an issue in the repository.