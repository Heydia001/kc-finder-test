import cv2
import numpy as np
import os
import matplotlib.pyplot as plt
import time
import glob
from pathlib import Path

DATABASE_IMAGES_DIR = Path("C:/KDH/kc-finder-test/database_images/")
TARGET_IMAGES_DIR = Path("C:/KDH/kc-finder-test/target_images/")
RESULTS_DIR = Path("C:/KDH/kc-finder-test/histogram_results/")
IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png']


def setup_directories():
    for directory in [DATABASE_IMAGES_DIR, TARGET_IMAGES_DIR, RESULTS_DIR]:
        directory.mkdir(exist_ok=True, parents=True)


def calculate_histogram(image, bins=16):
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    channels = []

    for i, range_val in enumerate([(0, 180), (0, 256), (0, 256)]):
        hist = cv2.calcHist([hsv_image], [i], None, [bins], range_val)
        hist = cv2.normalize(hist, hist, 0, 1, cv2.NORM_MINMAX)
        channels.append(hist)

    return np.concatenate(channels, axis=0)


def get_image_list(directory):
    image_paths = []
    for ext in IMAGE_EXTENSIONS:
        image_paths.extend(directory.glob(f"*{ext}"))
    return image_paths


def load_image(image_path):
    img = cv2.imread(str(image_path))
    return img


def compare_images(target_hist, database_path):
    img = load_image(database_path)
    if img is None:
        return None

    db_hist = calculate_histogram(img)
    similarity = cv2.compareHist(db_hist, target_hist, cv2.HISTCMP_CORREL)
    is_match = similarity >= 0.7

    return {
        'path': database_path,
        'name': database_path.name,
        'similarity': similarity,
        'is_match': is_match
    }


def display_top_matches(target_name, matches, result_folder):
    plt.figure(figsize=(15, 8))

    for i, match in enumerate(matches[:5]):
        plt.subplot(1, 5, i + 1)
        img = load_image(match['path'])
        plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        plt.title(f"{i + 1}. Similarity: {match['similarity']:.4f}\n{match['name'][:15]}")
        plt.axis('off')

    plt.tight_layout()
    result_path = result_folder / f"similar_images_{target_name}.jpg"
    plt.savefig(str(result_path), dpi=150, bbox_inches='tight')
    plt.close()


def process_target(target_path, result_folder):
    target_img = load_image(target_path)
    if target_img is None:
        return

    target_hist = calculate_histogram(target_img)
    database_images = get_image_list(DATABASE_IMAGES_DIR)

    matches = []
    for db_path in database_images:
        result = compare_images(target_hist, db_path)
        if result:
            matches.append(result)

    matches.sort(key=lambda x: x['similarity'], reverse=True)
    display_top_matches(target_path.name, matches, result_folder)


def main():
    setup_directories()

    target_images = get_image_list(TARGET_IMAGES_DIR)
    if not target_images:
        return

    timestamp = time.strftime("%Y%m%d-%H%M%S")
    result_folder = RESULTS_DIR / timestamp
    result_folder.mkdir(exist_ok=True)

    for target_path in target_images:
        process_target(target_path, result_folder)


if __name__ == "__main__":
    main()