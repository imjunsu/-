import os
import shutil

import kagglehub


DATASET = "hubertsidorowicz/football-players-stats-2025-2026"
SOURCE_FILE = "players_data_light-2025_2026.csv"
TARGET_FILE = "top5_leagues_player.csv"


def main():
    dataset_dir = kagglehub.dataset_download(DATASET)
    source_path = os.path.join(dataset_dir, SOURCE_FILE)
    if not os.path.exists(source_path):
        raise FileNotFoundError(f"데이터 파일을 찾지 못했습니다: {source_path}")

    shutil.copyfile(source_path, TARGET_FILE)
    print(f"완료: {TARGET_FILE}")


if __name__ == "__main__":
    main()
