import argparse
import json

from agent.style_agent import PersonalStyleAgent
from tools.wardrobe import add_item

def main():
    parser = argparse.ArgumentParser(description="Personal Style Agent MVP")
    sub = parser.add_subparsers(dest="command")

    p_add = sub.add_parser("add-item")
    p_add.add_argument("--name", required=True)
    p_add.add_argument("--type", required=True, choices=["top", "bottom", "shoes", "outerwear", "accessory"])
    p_add.add_argument("--color", default="")
    p_add.add_argument("--temp-min", type=float, default=-50)
    p_add.add_argument("--temp-max", type=float, default=60)
    p_add.add_argument("--avoid-rain", action="store_true")

    p_rec = sub.add_parser("recommend")
    p_rec.add_argument("--temp", type=float, required=True)
    p_rec.add_argument("--rain", action="store_true")
    p_rec.add_argument("--occasion", default="daily")

    p_fb = sub.add_parser("feedback")
    p_fb.add_argument("--outfit-id", required=True)
    p_fb.add_argument("--text", required=True)
    p_fb.add_argument("--score", type=float)

    args = parser.parse_args()

    if args.command == "add-item":
        item = add_item(args.name, args.type, args.color, args.temp_min, args.temp_max, args.avoid_rain)
        print(json.dumps(item, ensure_ascii=False, indent=2))
        return

    agent = PersonalStyleAgent()

    if args.command == "recommend":
        print(json.dumps(agent.recommend(args.temp, args.rain, args.occasion), ensure_ascii=False, indent=2))
    elif args.command == "feedback":
        agent.record_feedback(args.outfit_id, args.text, args.score)
        print("feedback recorded")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
