#!/usr/bin/env python3
"""Demo: Multi-session management.

Run with: python demos/demo_session.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from harness.session.manager import SessionManager

def main():
    print("=" * 50)
    print("  Multi-Session Demo")
    print("=" * 50)

    mgr = SessionManager(storage_dir=".demo_sessions")

    print("\n1. Creating sessions:")
    s1 = mgr.create_session("Python Coding")
    s2 = mgr.create_session("AI Research")
    print(f"   Session 1: [{s1.id}] {s1.title}")
    print(f"   Session 2: [{s2.id}] {s2.title}")

    print("\n2. Adding messages:")
    s1.add_message("user", "How to use decorators in Python?")
    s1.add_message("assistant", "Decorators are functions that modify...")
    s2.add_message("user", "Explain transformer attention mechanism")

    print("\n3. All sessions:")
    for s in mgr.list_sessions():
        act = " *" if s.id == mgr._active_session_id else ""
        print(f"   [{s.id}] {s.title} ({len(s.messages)} msgs){act}")

    print("\n4. Switch to session 1:")
    mgr.switch_session(s1.id)
    active = mgr.get_active()
    print(f"   Active: {active.title}")
    for m in active.get_history():
        print(f"   {m['role']}: {m['content'][:60]}")

if __name__ == "__main__":
    main()
