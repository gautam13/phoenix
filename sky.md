# Sky
_(engine -> bot)_

All calls that engine makes on a bot process are part of this API. The calls might be executed as passing strings/binary-msg/JSON objects over a `medium` (named pipes or using a messaging framework like `zmq`).  
All actions here are being performed by the engine.

**get_move(bot_id, turn_number, timeout)**
:   Activates `bot_id` process and requests bot to compute a move and write a JSON_OBJ to the _`medium`_. The process is then suspended (not necessarily explicitly).
If a valid move is not found on the _`medium`_ within `timeout` seconds, the bot forgoes this "turn" and is suspended.
A \\(penalty_{invalid-move}\\) is awarded if move is invalid or incomplete.
A \\(penalty_{no-move}\\) is awarded is _`medium`_ is found empty.
>Note:
Scores are not handled by the Game only, but also by the engine.
This is to handle the case when a bot has been disqualified by the Engine but the Game believes that bot is just sitting there not making a move. Game will score such a bot according to it's scoring strategy but that score is meaningless.
On the other hand, a bot might _actually_ be unresponsive, and the scores awarded by the Game would have _actual_ meaning.
**That's why scores are affected by both Game and Engine. It might make sense to keep scoring _outside_ the Game altogether...**

**update_game_state(bot_id, turn_number, new_state)**
:   The engine sends the `new_state` (of the game) to the bot via the _`medium`_. This `new_state` was procured (and is forwarded) from the game when moves of \\(turn number - 1\\) were executed by the game. This need not be a JSON object as it is game-dependent.
**Expects** `bot_id` process to acknowledge receipt by writing `OK` or :+1: to the _`medium`_.
>Note:
`game-state` must contain scores too.

**append_logs(bot_id, turn_number, logs)**
:   `logs` is a container (`dict`) of various log-channels like `info-from-game`, `move-errors`, etc. that were generated by the game while executing \\(turn number\\) moves.
>Note:
`logs` need not be the same for every `bot_id` for a given turn, and that depends solely on the game.

**init_bot(bot_id, timeout)**
:   Launches the bot process and disqualifies it if an acknowledge (like `OK` or :+1:) is not found on the _`medium`_ after `timeout` seconds.

**suspend_bot(bot_id)**
:   Suspends the bot process (if currently active).

**kill_bot(bot_id)**
:   Kills the bot process.

**resume_bot(bot_id)**
:   Resumes the bot process (if suspended earlier).

**game_over(bot_id)**
:   When a bot is unable to make a move it is said to be "defeated". Engine inspects the `game-state` at each turn to kill bots that have been "defeated".
Engine appends a game-summary to the `logs` (when `append_logs`) is called.

**init_syscall_filter()**
:   This function is called just after fork() and just before execlp(). It initializes the seccomp filter and filters out system calls.

***Any more?***

# Appendix

`logs`
:   Are accessible to the bot when it is making a move.
Are returned to the team along with the game-replay and summary.

`game-state`
:   `Schema(game-stuff[], scores[], game-statuses[])`
`game-stuff` is game dependent. Engine doesn't care about the contents.

* If `game-stuff` is a list of \\(size = no. of bots\\), each bot (might) have different `game-stuff` as result of **"game-fog"**.
* If `game-stuff` is not a list, each bot gets the same `game-stuff`.

`game-status`
:   Bot's in-game status. Whether they are still in the game or not. Decided by the game.

`bot-status`
:   Bot process status. Decided by the Engine.

* active
* suspended
* busy
* unresponsive
* disqualified
* _more?_