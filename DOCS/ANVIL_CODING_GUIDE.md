# ANVIL CODING DOCTRINE: THE MICRO-CHUNK STRATEGY
## "Don't Boil the Ocean. Forge the Nail."

### 1. THE MANDATE
Legacy software (e.g., Vim, Linux Kernel) is too large to "port" in one pass. Hallucination rates increase exponentially with LoC (Lines of Code).
**We must decompose targets into atomic, verifiable units.**

### 2. THE PROCESS (CARDING)
Every feature is a Card. Every Card produces **one** `.mpy` artifact.

#### BAD CARD (Too Big)
> "Port Vim to Anvil."
> *Result:* Failure. Infinite loops. Hallucinated C libraries.

#### GOOD CARD (Micro-Chunk)
> "Implement `TextBuffer` class in Anvil Python."
> *Deliverables:*
> 1. `buffer.py`: A class that holds a list of strings.
> 2. `tests/test_buffer.py`: Verifies `insert_line`, `delete_line`.
> 3. `anvil build buffer.py` -> `buffer.mpy`.
> *Execution:* Use `/usr/local/bin/anvil` for all runtime verification.

### 3. THE VIM-LITE ROADMAP (EXAMPLE)
To forge a Sovereign Editor, we do not start with UI. We start with Data Structures.
...
**RULE:** If it takes more than 100 lines of Python, split the card.
**RUNTIME:** The system binary is located at `/usr/local/bin/anvil`. Use this for all cards unless a recompile is explicitly requested.
