import csv
from ultralytics import YOLO
from matplotlib.path import Path
import ast
import argparse
from pathlib import Path as FilePath
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_config(file_path):
    """Load configuration from file."""
    with open(file_path, "r") as f:
        polygons = ast.literal_eval(f.readline())
        polygon_pairs = ast.literal_eval(f.readline())
        video_path = f.readline().strip()
    return polygons, polygon_pairs, video_path

def track_cars_through_polygons(results, polygon_pairs, polygons):
    """
    Track unique car IDs passing through specified pairs of polygons.

    :param results: Stream of detection results from YOLO.
    :param polygon_pairs: List of tuples indicating pairs of polygons to check intersections.
    :param polygons: List of lists containing polygon vertex points.
    :return: Dictionary of sets with unique car IDs that entered both polygons in each pair.
    """
    polygon_paths = [Path(poly) for poly in polygons]
    cars_in_polygons = {i: set() for i in range(len(polygons))}

    for result in results:
        if result.boxes.data.shape[0] > 0:
            for box, conf, cls_id, track_id in zip(result.boxes.xyxy, result.boxes.conf, result.boxes.cls, result.boxes.id):
                if cls_id == 2 and track_id is not None:  # Assuming class 2 is 'car'
                    center_point = ((box[0] + box[2]) / 2, (box[1] + box[3]) / 2)
                    for poly_index, poly_path in enumerate(polygon_paths):
                        if poly_path.contains_point(center_point):
                            cars_in_polygons[poly_index].add(track_id.item())

    return {pair: cars_in_polygons[pair[0]].intersection(cars_in_polygons[pair[1]]) for pair in polygon_pairs}

def save_results_to_csv(cars_passing_pairs, output_file):
    """Save results to a CSV file."""
    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Polygon Pair', 'Number of Unique Cars', 'Car IDs'])
        for pair, cars in cars_passing_pairs.items():
            writer.writerow([str(pair), len(cars), ', '.join(map(str, cars))])
    logging.info(f"Results saved to {output_file}")

def main(config_file, model_path, output_file):
    polygons, polygon_pairs, video_path = load_config(config_file)
    
    logging.info("Loading YOLO model...")
    model = YOLO(model_path)
    
    logging.info("Starting car tracking...")
    results = model.track(source=video_path, show=True, tracker="bytetrack.yaml", classes=[2,7])
    
    logging.info("Processing tracking results...")
    cars_passing_pairs = track_cars_through_polygons(results, polygon_pairs, polygons)
    
    for pair, cars in cars_passing_pairs.items():
        logging.info(f"Cars that passed through polygons {pair}: {len(cars)} unique IDs.")
    
    save_results_to_csv(cars_passing_pairs, output_file)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Track cars through polygons using YOLO.")
    parser.add_argument("--config", type=str, default="polygons_combinations.txt", help="Path to configuration file")
    parser.add_argument("--model", type=str, default="yolov9e.pt", help="Path to YOLO model")
    parser.add_argument("--output", type=str, default="car_tracking_results.csv", help="Path to output CSV file")
    args = parser.parse_args()

    main(args.config, args.model, args.output)