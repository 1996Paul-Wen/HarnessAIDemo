#!/usr/bin/env python3
"""Demo: Skill system - loading and using markdown-defined skills.

Run with: python demos/demo_skills.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from harness.skill.loader import SkillLoader

def main():
    print("=" * 50)
    print("  Skill System Demo")
    print("=" * 50)

    loader = SkillLoader(skills_dir="demos/skills")

    print("\n1. Discovering skills...")
    found = loader.discover()
    print(f"   Found: {found}")

    print("\n2. Loading skills...")
    skills = loader.load_all()
    for name, skill in skills.items():
        print(f"   {skill.to_description()}")

    print("\n3. Applying skill to user request:")
    for name, skill in skills.items():
        prompt = skill.apply_to_prompt("Summarize this AI article.")
        print(f"\n   [{skill.name}]:")
        print(f"   {prompt[:200]}...")

if __name__ == "__main__":
    main()
