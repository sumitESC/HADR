# Lightning-Fast OSM Extractor for Google Colab

This script uses the C++ `osmium-tool` binary (which is easily available on Colab's Linux environment) to crop the 700MB India PBF into 49 tiny files in just seconds.

### How to use this on Google Colab:

1. Open [Google Colab](https://colab.research.google.com/) and create a **New Notebook**.
2. On the left side of Colab, click the **Folder icon** to open the File Browser.
3. Upload two files from your computer to Colab:
   *   `colab_extractor.py` (from this folder)
   *   `dams.json` (from your `backend/data/dams/` folder)
4. In the first cell of your Colab notebook, paste this exact command and hit Run (Shift+Enter):
   ```python
   !python colab_extractor.py
   ```
5. **That's it!** The script will automatically:
   * Install the C++ Osmium tool
   * Download the latest 700MB India PBF file automatically
   * Extract all 49 dams in less than 3 minutes
   * Create a `osm_results.zip` file containing all your `.geojson` files
6. Right-click `osm_results.zip` in the Colab file browser and click **Download**.
7. Extract the downloaded zip, and move the `settlements/` and `rivers/` files into your project's `backend/data/` folder!
