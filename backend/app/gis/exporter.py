import json
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

class Exporter:
    @staticmethod
    def export_geojson(geojson_data: dict, output_path: Path):
        """Saves GeoJSON FeatureCollection to file."""
        with open(output_path, "w") as f:
            json.dump(geojson_data, f, indent=2)
        return output_path

    @staticmethod
    def export_kml(geojson_data: dict, output_path: Path, title: str = "Flood Inundation Extent"):
        """Converts GeoJSON features to valid KML XML file."""
        kml_ns = "http://www.opengis.net/kml/2.2"
        root = ET.Element(f"{{{kml_ns}}}kml")
        doc = ET.SubElement(root, f"{{{kml_ns}}}Document")
        
        doc_name = ET.SubElement(doc, f"{{{kml_ns}}}name")
        doc_name.text = title
        
        # Style definition (Semi-transparent red fill for flood extent)
        style = ET.SubElement(doc, f"{{{kml_ns}}}Style", id="floodStyle")
        poly_style = ET.SubElement(style, f"{{{kml_ns}}}PolyStyle")
        color = ET.SubElement(poly_style, f"{{{kml_ns}}}color")
        color.text = "7f0000ff" # 50% opacity red (ABGR format)
        line_style = ET.SubElement(style, f"{{{kml_ns}}}LineStyle")
        lcolor = ET.SubElement(line_style, f"{{{kml_ns}}}color")
        lcolor.text = "ff0000ff"
        lwidth = ET.SubElement(line_style, f"{{{kml_ns}}}width")
        lwidth.text = "2"

        features = geojson_data.get("features", [])
        for idx, feat in enumerate(features):
            geom = feat.get("geometry", {})
            props = feat.get("properties", {})
            
            if geom.get("type") in ["Polygon", "MultiPolygon"]:
                placemark = ET.SubElement(doc, f"{{{kml_ns}}}Placemark")
                pname = ET.SubElement(placemark, f"{{{kml_ns}}}name")
                pname.text = f"Flood Zone - T+{props.get('timestep_min', 0)} min"
                
                style_url = ET.SubElement(placemark, f"{{{kml_ns}}}styleUrl")
                style_url.text = "#floodStyle"
                
                # Coordinates extraction
                coords_list = []
                if geom["type"] == "Polygon":
                    coords_list = [geom["coordinates"][0]]
                elif geom["type"] == "MultiPolygon":
                    coords_list = [p[0] for p in geom["coordinates"]]
                    
                for cring in coords_list:
                    polygon_elem = ET.SubElement(placemark, f"{{{kml_ns}}}Polygon")
                    outer = ET.SubElement(polygon_elem, f"{{{kml_ns}}}outerBoundaryIs")
                    lring = ET.SubElement(outer, f"{{{kml_ns}}}LinearRing")
                    coords_elem = ET.SubElement(lring, f"{{{kml_ns}}}coordinates")
                    
                    coord_str_items = [f"{lon},{lat},0" for lon, lat in cring]
                    coords_elem.text = " ".join(coord_str_items)

        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ")
        tree.write(output_path, encoding="utf-8", xml_declaration=True)
        return output_path

    @staticmethod
    def export_shp_zip(geojson_data: dict, output_zip_path: Path):
        """
        Creates GIS Shapefile bundle package (.zip) containing GeoJSON layer, PRJ, and metadata.
        """
        geojson_path = output_zip_path.parent / "flood_extent.geojson"
        prj_path = output_zip_path.parent / "flood_extent.prj"
        
        with open(geojson_path, "w") as f:
            json.dump(geojson_data, f, indent=2)
            
        # WGS84 WKT projection info
        prj_content = 'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433]]'
        with open(prj_path, "w") as f:
            f.write(prj_content)
            
        with zipfile.ZipFile(output_zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(geojson_path, arcname="flood_extent.geojson")
            zf.write(prj_path, arcname="flood_extent.prj")
            
        return output_zip_path
