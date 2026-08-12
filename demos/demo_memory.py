#!/usr/bin/env python3
"""Demo: Memory system (short-term, long-term, hybrid, session isolation, global).

Run with: python run.py memory
      or: python demos/demo_memory.py
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from harness.memory import ShortTermMemory, LongTermMemory, HybridMemory

# ---------------------------------------------------------------------------
# Demo storage paths (all covered by .gitignore via .demo*)
# ---------------------------------------------------------------------------
LTM_STORAGE = ".demoMemory/long_term_memory_store.json"
HYBRID_STORAGE = ".demoMemory/hybrid_memory.json"
PERSIST_STORAGE = ".demoMemory/persist_memory.json"
SESSION_STORAGE = ".demoMemory/sessions"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _header(title: str) -> None:
    """Print a step header."""
    print(f"\n{'=' * 50}")
    print(f"  {title}")
    print(f"{'=' * 50}")


def _store(memory, entries: list[tuple[str, str]], indent: str = "  ") -> None:
    """Add entries to a memory instance and print each one."""
    for role, content in entries:
        memory.add(role, content)
        prefix = f"{role}: " if role == "assistant" else ""
        print(f"{indent}+ {prefix}{content[:60]}{'...' if len(content) > 60 else ''}")


def _print_results(results: list[dict], tag_key: str = "source") -> None:
    """Print search results with source tags."""
    if not results:
        print("    (no results)")
        return
    for r in results:
        tag = r.get(tag_key, "memory").upper()
        text = r["content"] if isinstance(r, dict) else r.content
        print(f"    [{tag:>7s}] {text[:55]}{'...' if len(text) > 55 else ''}")


# ===========================================================================
# Step 1: Short-Term Memory
# ===========================================================================
def demo_short_term():
    _header("Step 1: Short-Term Memory (FIFO Buffer)")
    print("  Capacity = 5 messages. Oldest are evicted when full.\n")

    stm = ShortTermMemory(capacity=5)

    messages = [
        ("user", "What is Python?"),
        ("assistant", "Python is a high-level programming language."),
        ("user", "What about decorators?"),
        ("assistant", "Decorators wrap functions to extend behavior."),
        ("user", "How do generators work?"),
        ("assistant", "Generators use yield for lazy evaluation."),
        ("user", "What are context managers?"),
    ]
    _store(stm, messages)

    print(f"\n  Buffer ({len(stm)}/{stm.capacity}):")
    for item in stm.get_all():
        print(f"    {item.role}: {item.content[:50]}")

    print("\n  Search 'decorators':")
    _print_results([{"source": "stm", "content": r.content} for r in stm.search("decorators")])


# ===========================================================================
# Step 2: Long-Term Memory
# ===========================================================================
def demo_long_term():
    _header("Step 2: Long-Term Memory (TF-IDF + Persistence)")

    ltm = LongTermMemory(storage_path=LTM_STORAGE)
    ltm.clear()

    knowledge = [
        ("user", "I prefer using TypeScript over JavaScript for large projects."),
        ("assistant", "TypeScript adds static typing which helps catch errors early."),
        ("user", "My favorite design pattern is the observer pattern."),
        ("assistant", "The observer pattern is great for event-driven architectures."),
        ("user", "I work at a fintech company building payment systems."),
        ("assistant", "Payment systems require high reliability and security."),
        ("user", "We use Kubernetes for container orchestration in production."),
        ("assistant", "K8s provides auto-scaling, self-healing, and service discovery."),
        ("user", "Our team follows trunk-based development workflow."),
        ("assistant", "Trunk-based development reduces merge conflicts and speeds up releases."),
    ]
    print("  Storing 10 knowledge items:")
    _store(ltm, knowledge, indent="    ")

    for q in ["TypeScript and JavaScript", "payment and security", "Kubernetes and deployment"]:
        print(f"\n  Search: '{q}'")
        for i, r in enumerate(ltm.search(q, top_k=2), 1):
            print(f"    #{i}: {r.content[:60]}...")

    print(f"\n  Persisted to: {LTM_STORAGE}")


# ===========================================================================
# Step 3: Hybrid Memory
# ===========================================================================
def demo_hybrid():
    _header("Step 3: Hybrid Memory (Short-Term + Long-Term)")

    memory = HybridMemory(short_term_capacity=4, storage_path=HYBRID_STORAGE)
    memory.clear()

    conversation = [
        ("user", "I'm learning Rust programming language."),
        ("assistant", "Rust focuses on safety, speed, and concurrency."),
        ("user", "How does Rust's ownership system work?"),
        ("assistant", "Ownership prevents data races at compile time."),
        ("user", "What about async/await in Rust?"),
        ("assistant", "Rust uses tokio or async-std for async runtime."),
        ("user", "Now let's talk about databases."),
        ("assistant", "Sure, what kind of databases are you interested in?"),
        ("user", "I want to compare PostgreSQL and MongoDB."),
        ("assistant", "PostgreSQL is relational, MongoDB is document-based."),
    ]
    print("  10 messages added (short-term capacity = 4):\n")
    _store(memory, conversation, indent="    ")

    print(f"\n  Short-term buffer: {len(memory.get_recent(100))} messages")
    print(f"  Long-term store:   {len(memory.long_term)} messages")

    for query in ["Rust ownership", "database comparison"]:
        print(f"\n  Context for '{query}':")
        context = memory.get_relevant_context(query, n_recent=4, n_relevant=3)
        for line in context.split("\n"):
            print(f"    {line}")


# ===========================================================================
# Step 4: Persistence
# ===========================================================================
def demo_persistence():
    _header("Step 4: Persistence (Survives Restart)")

    print("  [Store] Creating memory and storing items...")
    mem1 = LongTermMemory(storage_path=PERSIST_STORAGE)
    mem1.clear()
    _store(mem1, [
        ("user", "My name is Alice and I'm a backend engineer."),
        ("user", "I prefer Vim as my text editor."),
        ("user", "I'm working on a distributed caching project."),
    ], indent="    ")
    del mem1  # simulate shutdown

    print("\n  [Reload] Recreating from disk (simulating restart)...")
    mem2 = LongTermMemory(storage_path=PERSIST_STORAGE)
    print(f"    Loaded {len(mem2)} items from {PERSIST_STORAGE}")

    for q in ["editor", "caching"]:
        print(f"\n  Search '{q}':")
        _print_results([{"source": "disk", "content": r.content} for r in mem2.search(q)])


# ===========================================================================
# Step 5: Session Isolation + Global Memory
# ===========================================================================
def demo_session_and_global():
    """The full picture: each session has isolated memory, and a shared global
    memory provides cross-session context.  Combined search merges both layers.
    """
    from harness.session.manager import SessionManager

    _header("Step 5: Session Isolation + Global Memory")
    print("  Architecture:")
    print("    global_memory.json  -- shared across all sessions")
    print("    <session>/memory.json -- isolated per session")
    print("    search_memories()   -- merges global + session results\n")

    # -- Setup ---------------------------------------------------------------
    mgr = SessionManager(storage_dir=SESSION_STORAGE)
    for s in mgr.list_sessions():
        # Delete existing sessions to start fresh
        mgr.delete_session(s.id)

    s1 = mgr.create_session("Python Project")
    s2 = mgr.create_session("Cooking Recipes")

    # -- Store session-specific knowledge (isolated) -------------------------
    print(f"  [{s1.title}] Session memory:")
    _store(mgr.get_memory(s1.id), [
        ("user", "We use FastAPI with uvicorn for our API server."),
        ("user", "Our test framework is pytest with fixtures."),
        ("user", "I prefer Python type hints with mypy."),
    ], indent="    ")

    print(f"\n  [{s2.title}] Session memory:")
    _store(mgr.get_memory(s2.id), [
        ("user", "I'm learning to make sushi at home."),
        ("user", "I prefer Japanese cuisine over Italian."),
        ("user", "Fresh pasta needs flour, eggs, and a pasta machine."),
    ], indent="    ")

    # -- Store global knowledge (shared) -------------------------------------
    print("\n  [Global Memory] User-level knowledge (shared across all sessions):")
    mgr.global_memory.clear()
    _store(mgr.global_memory, [
        ("user", "My name is Alice. I'm a senior backend engineer."),
        ("user", "I prefer concise answers with code examples."),
        ("user", "I use macOS and Vim as my daily tools."),
    ], indent="    ")

    # -- Demonstrate combined search -----------------------------------------
    searches = [
        ("engineer tools", s1.id, "Global results appear in Python session"),
        ("engineer tools", s2.id, "Same global results appear in Cooking session"),
        ("pytest",         s1.id, "Session result found in Python"),
        ("pytest",         s2.id, "Session result NOT found in Cooking (isolated)"),
        ("sushi",          s1.id, "Session result NOT found in Python (isolated)"),
        ("sushi",          s2.id, "Session result found in Cooking"),
    ]
    for query, sid, description in searches:
        session = mgr._sessions[sid]
        print(f"\n  search_memories('{query}', session={session.title}):")
        print(f"    # {description}")
        _print_results(mgr.search_memories(query, session_id=sid))

    # -- Storage layout ------------------------------------------------------
    print(f"\n  Storage layout:")
    print(f"    {SESSION_STORAGE}/global_memory.json")
    for s in mgr.list_sessions():
        print(f"    {SESSION_STORAGE}/{s.id}/memory.json  ({s.title})")

    # -- Cleanup (commented out -- uncomment to remove demo artifacts) -------
    # for s in mgr.list_sessions():
    #     mgr.delete_session(s.id)
    # global_path = os.path.join(SESSION_STORAGE, "global_memory.json")
    # if os.path.exists(global_path):
    #     os.remove(global_path)


# ===========================================================================
# Main
# ===========================================================================
def main():
    print("=" * 50)
    print("  Memory System Demo")
    print("  Short-Term | Long-Term | Hybrid | Isolation | Global")
    print("=" * 50)

    demo_short_term()
    demo_long_term()
    demo_hybrid()
    demo_persistence()
    demo_session_and_global()

    print(f"\n{'=' * 50}")
    print("  Memory Demo complete!")
    print(f"{'=' * 50}")


if __name__ == "__main__":
    main()
