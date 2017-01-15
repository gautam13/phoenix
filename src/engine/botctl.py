import os
from signal import SIGCONT, SIGSTOP, SIGTERM
from time import sleep
import sys

class BotState:
    """Bot process status. Decided by the Engine."""
    active = 0
    suspended = 1
    busy = 2
    unresponsive = 3
    disqualified = 4

# defined as sky
class Botctl:
    def __init__(self, timeout=0.2, args):
        """Launches the bot process. timeout (seconds, float accepted) is the 
        time for which the engine waits for the bot to acknowledge i.e. send
        "I'm Poppy!" in the medium (anonymous pipe here). args should be a list,
        example: ['/usr/bin/python', 'python', 'bot1.py'] this will be 
        directly executed with execlp. It also initiates the seccomp-bpf filter
        to restrict the system calls that can be used by the bot. Resources such
        as stack and heap or the whole memory is given an upper limit here. We
        also pipe the STDIN and STDOUT of the bot to some file that can be
        manipulated by the engine.
        """

        self.BOTIN_CHILD, self.BOTIN_PARENT = os.pipe()
        self.BOTOUT_PARENT, self.BOTOUT_CHILD = os.pipe()

        # the stderr is redirected here and logged
        self.bot_err_log = open('bot_err_log.txt', 'w')

        self.moves = []
        self.bot_status = BotState.active
        self.bot_pid = os.fork()
        
        if self.bot_pid == 0:
            os.close(self.BOTIN_PARENT)
            os.close(self.BOTOUT_PARENT)

            os.dup2(self.BOTIN_CHILD, sys.stdin.fileno())
            os.dup2(self.BOTOUT_CHILD, sys.stdout.fileno())
            os.dup2(self.bot_err_log.fileno(), sys.stderr.fileno())

            self.bot_err_log.close()

            # seccomp filter
            # memory management
            execl(*args)
        else:
            os.close(self.BOTIN_CHILD)
            os.close(self.BOTOUT_CHILD)
            self.bot_err_log.close()
            
            self.botin = fdopen(self.BOTIN_PARENT, 'w')
            self.botout = fdopen(self.BOTOUT_PARENT, 'r')
            self.bot_move_log = open('bot_move_log.txt', 'w')

            sleep(timeout)

            if self.get_move() == "I'm Poppy!":
                print "Bot acknowledged"
            else:
                self.bot_status = BotState.unresponsive
                print "Bot unresponsive"

    def suspend_bot(self):
        """ Suspends the bot process (if currently active)."""
        
        os.kill(self.bot_pid, SIGSTOP)

    def resume_bot(self):
        """Resumes the bot process (if suspended earlier)."""
        
        os.kill(self.bot_pid, SIGCONT)

    def kill_bot(self):
        """ Kills the bot process."""
        
        os.kill(self.bot_pid, SIGTERM)

    def get_move(self):
        """Requests bot to compute a move and write a JSON_OBJ to the medium. The 
        process is then suspended (not necessarily explicitly). If a valid move is
        not found on the medium within timeout seconds, the bot forgoes this "turn"
        and is suspended. A (penalty or invalid-move) is awarded if move is invalid
        or incomplete. A (penalty or no-move) is awarded is medium is found empty.
        """
        
        move =  self.botout.read()
        self.moves.append(move)
        return move

    def update_game_state(self, new_state):
        """new_state is a sting. The engine sends the new_state (of the game) to
        the bot via the medium. This new_state was procured (and is forwarded)
        from the game when moves of (turn number - 1) were executed by the game.
        This need not be a JSON object as it is game-dependent. Expects bot
        process to acknowledge receipt by writing to the medium."""
        
        self.botin.write(new_state)

    def append_logs(self):
        """logs is a container (list) of various log-channels like info-from-game,
        move-errors, etc. that were generated by the game while executing (turn number)
        moves."""
        
        self.bot_move_log.write('\n'.join(moves))

    def game_over(self):
        """When a bot is unable to make a move it is said to be "defeated".
        Engine inspects the game-state at each turn to kill bots that have
        been "defeated". Engine appends a game-summary to the logs (when 
        append_logs) is called. Also closes all the file descriptors."""
        
        self.botin.close()
        self.botout.close()
        
        self.append_logs()
        self.bot_move_log.close()

        self.kill_bot()
