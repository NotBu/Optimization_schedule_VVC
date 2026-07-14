"""Functions for implementing the rules of the classic arcade game Pac-Man."""


def eat_ghost(power_pellet_active, touching_ghost):
    """Verify that Pac-Man can eat a ghost if he is empowered by a power pellet."""
    if power_pellet_active == True and touching_ghost == True:
        return True
    elif power_pellet_active == False and touching_ghost == True :
        return False
    else :
        return False

def score(touching_power_pellet, touching_dot):
    """Verify that Pac-Man has scored when a power pellet or dot has been eaten."""
    return touching_power_pellet or touching_dot



def lose(power_pellet_active, touching_ghost):
    """Trigger the game loop to end (GAME OVER) when Pac-Man touches a ghost without his power pellet."""
    if power_pellet_active == False and touching_ghost == True:
        return True
    elif power_pellet_active == True and touching_ghost == True :
        return False
    else :
        return False

def win(has_eaten_all_dots, power_pellet_active, touching_ghost):
    """Trigger the victory event when all dots have been eaten.

    Parameters:
        has_eaten_all_dots (bool): Has the player "eaten" all the dots?
        power_pellet_active (bool): Does the player have an active power pellet?
        touching_ghost (bool): Is the player touching a ghost?

    Returns:
        bool: Has the player won the game?
    """

    pass
    if has_eaten_all_dots == True and power_pellet_active == True and touching_ghost == False:
        return True
    elif power_pellet_active == True and has_eaten_all_dots == True and touching_ghost == True :
        return True
    elif power_pellet_active == False and has_eaten_all_dots == True and touching_ghost == False :
        return True
    else : 
        return False