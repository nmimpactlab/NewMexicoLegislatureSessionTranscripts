# Deployment Instructions for GitHub Pages

## Automatic Deployment

Once you merge the pull request to your main branch, follow these steps to enable GitHub Pages:

### Step 1: Enable GitHub Pages

1. Go to your repository on GitHub: `https://github.com/nmimpactlab/NewMexicoLegislatureSessionTranscripts`
2. Click on **Settings** (top navigation)
3. Scroll down to **Pages** in the left sidebar
4. Under **Source**, select:
   - Branch: `main` (or your default branch)
   - Folder: `/docs`
5. Click **Save**

### Step 2: Wait for Deployment

GitHub will automatically build and deploy your site. This usually takes 1-2 minutes.

You'll see a message like:
```
Your site is ready to be published at https://nmimpactlab.github.io/NewMexicoLegislatureSessionTranscripts/
```

### Step 3: Access Your Site

Once deployed, your searchable database will be available at:
```
https://nmimpactlab.github.io/NewMexicoLegislatureSessionTranscripts/
```

## What Was Built

### Main Search Interface
- **URL**: `/` or `/index.html`
- **Features**:
  - Search box with keyword search
  - Filters for committee, year, bill, and speaker
  - Session listings with metadata
  - Bill, speaker, and committee browsing
  - Sortable results

### Analytics Dashboard
- **URL**: `/analytics.html`
- **Features**:
  - Key insights summary
  - Sessions by year chart
  - Top committees chart
  - Most discussed bills
  - Most active speakers
  - Monthly and day-of-week distributions

### Data Files
- `index.json` (22MB) - Full searchable index
- `index.json.gz` (3.8MB) - Compressed version

## Rebuilding the Index

If you add new transcript files, rebuild the index:

```bash
python3 build_index.py
```

This will regenerate `docs/index.json` and `docs/index.json.gz`.

## File Structure

```
docs/
├── index.html          # Main search interface
├── analytics.html      # Analytics dashboard
├── index.json          # Searchable index (22MB)
├── index.json.gz       # Compressed index (3.8MB)
└── _config.yml         # Jekyll configuration

build_index.py          # Index builder script
README.md               # Project documentation
```

## Troubleshooting

### Site not loading?
- Ensure GitHub Pages is enabled in Settings > Pages
- Check that the source is set to `/docs` folder
- Wait 1-2 minutes after enabling for initial deployment

### Search not working?
- Open browser developer console (F12)
- Check for any error messages
- Verify `index.json` is accessible at: `https://your-site/index.json`

### Need to update the index?
1. Run `python3 build_index.py`
2. Commit the updated `docs/index.json` and `docs/index.json.gz`
3. Push to your repository
4. GitHub Pages will automatically redeploy

## Performance Notes

- The index.json file is 22MB but loads efficiently in modern browsers
- First load may take 3-5 seconds to fetch the index
- Subsequent searches are instant (client-side)
- The compressed .gz version is available but not used by default (browsers handle compression)

## Customization

### Changing Colors
Edit the CSS in `docs/index.html` and `docs/analytics.html`

### Modifying Search Logic
Edit the JavaScript `performSearch()` function in `docs/index.html`

### Adding New Charts
Edit `docs/analytics.html` and add new Chart.js visualizations

## Support

For issues or questions, please create a GitHub issue in the repository.
