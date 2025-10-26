#!/usr/bin/env python3
import sys
import json
import shutil
from pathlib import Path
from datetime import datetime

WORK = Path(__file__).resolve().parents[1]
DATA_FILE = WORK / "data" / "plants.json"

def usage():
    print("사용법: save_plants.py <input.json>    또는 stdin으로 JSON 전달")
    sys.exit(2)

def main():
    if len(sys.argv) == 2:
        src = Path(sys.argv[1])
        if not src.exists():
            print("입력 파일이 없습니다:", src)
            sys.exit(1)
        text = src.read_text(encoding="utf-8")
    else:
        text = sys.stdin.read()
        if not text.strip():
            usage()

    try:
        obj = json.loads(text)
    except Exception as e:
        print("JSON 파싱 실패:", e)
        sys.exit(1)

    # 간단 검증: 최상위가 리스트인지 확인
    if not isinstance(obj, list):
        print("경고: 최상위 JSON 타입이 리스트가 아닙니다. 계속 저장하려면 확인하세요.")

    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    # 백업
    if DATA_FILE.exists():
        bak = DATA_FILE.with_name(DATA_FILE.name + ".bak." + datetime.utcnow().strftime("%Y%m%dT%H%M%SZ"))
        shutil.copy2(DATA_FILE, bak)
        print("백업 생성:", bak)
    try:
        DATA_FILE.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
        print("저장 완료:", DATA_FILE)
    except Exception as e:
        print("파일 쓰기 실패:", e)
        sys.exit(1)

if __name__ == "__main__":
    main()