#!/usr/bin/env python
import sys
import warnings

from crew import ResearchCrew

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# Default input used for local runs (`crewai run`).
# On AMP, the real value arrives via POST /kickoff {"inputs": {"question": "..."}}.
DEFAULT_INPUTS = {
    "question": "What are the main approaches to solid-state battery development and how close are they to commercialization?"
}


def run():
    """Run the crew locally."""
    try:
        result = ResearchCrew().crew().kickoff(inputs=DEFAULT_INPUTS)
        print("\n\n=== FINAL REPORT ===\n")
        print(result.raw)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")


def train():
    """Train the crew for a given number of iterations."""
    try:
        ResearchCrew().crew().train(
            n_iterations=int(sys.argv[1]),
            filename=sys.argv[2],
            inputs=DEFAULT_INPUTS,
        )
    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")


def replay():
    """Replay the crew execution from a specific task."""
    try:
        ResearchCrew().crew().replay(task_id=sys.argv[1])
    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")


def test():
    """Test the crew execution and return the results."""
    try:
        ResearchCrew().crew().test(
            n_iterations=int(sys.argv[1]),
            eval_llm=sys.argv[2],
            inputs=DEFAULT_INPUTS,
        )
    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")


if __name__ == "__main__":
    run()
