import random
import copy

def listOfIndexes(list, a):
    indexes = []
    i = 0
    while i < len(list) and a in list[i::]:
        index = list.index(a, i, len(list))
        indexes.append(index)
        i = index+1
    return indexes

#Returns a dictionnary containing as key the ids of the station that are used by several vehicles and as data
# the id of these vehicles
def isAcceptable(solution):
    problems = []
    cur = 0
    for i in solution:
        indexes = listOfIndexes(solution,i)
        if len(indexes) > 1:
            to_add = [i, indexes]
            if to_add not in problems:
                problems.append([i, indexes])
        cur += 1
    return problems

#solution_n_weight is a list of pairs of station numbers and weights
def solutionWeight(solution_n_weight):
    weight = 0
    for id_n_weight in solution_n_weight:
        weight += id_n_weight[1]
    return weight

def petitsChevauxList(nb_vehicles, nb_close_stations, total_nb_stations) :

    petits_chevaux_list = [[] for x in range(nb_vehicles)]
    total_station_nb_list = []
    for vehicle in petits_chevaux_list:
        station_nb_list = []
        weight = 0
        for i in range(0, nb_close_stations):
            rand_station_nb = random.randrange(1, total_nb_stations)
            while rand_station_nb in station_nb_list:
                rand_station_nb = random.randrange(1, total_nb_stations)

            if rand_station_nb not in total_station_nb_list:
                total_station_nb_list.append(rand_station_nb)

            station_nb_list.append(rand_station_nb)
            weight += random.random()
            vehicle.append([rand_station_nb, weight])

    print len(total_station_nb_list)
    if len(total_station_nb_list) < nb_vehicles:
        print "not enough stations"
        return petitsChevauxList(nb_vehicles, nb_close_stations, total_nb_stations)
    else:
        return petits_chevaux_list

def createSons(solution, problems, petits_chevaux_list, all_solutions):
    if len(problems) == 0:
        return [solution]

    rec = createSons(solution, problems[1::], petits_chevaux_list, all_solutions)
    to_rtn = []

    for el1 in problems[0][1]:
        for modify in rec:
            tmp = copy.copy(modify)
            for el2 in problems[0][1]:
                if (el2 != el1):
                    tmp = advanceStation(el2, problems[0][0], tmp, petits_chevaux_list)
            #Test if we aready visited this solution
            if not(all_solutions.has_key(str(removeWeight(tmp)))):
                all_solutions[str(removeWeight(tmp))] = 1
                to_rtn.append(tmp)
    return to_rtn

def advanceStation(ev_id, station_id, prev_sol, petits_chevaux_list):
    cur = 0
    for i in petits_chevaux_list[ev_id]:
        if i[0] == station_id:
            index = cur
            break
        cur +=1
    if index < len(petits_chevaux_list[ev_id])-1:
        next_station = petits_chevaux_list[ev_id][index+1]
        new_sol = list(prev_sol)
        new_sol[ev_id] = next_station
    return new_sol

def removeWeight(solution_with_weight):
    solution_without_weight = []
    for i in solution_with_weight:
        solution_without_weight.append(i[0])
    return solution_without_weight

#petits_chevaux_list = list of list of pairs generated by the function petitsChevauxList
def petitsChevauxAlg(petits_chevaux_list, max_nb_iter):

    solu = []
    w = float("inf")
    #Initial solution
    s = []
    s_without_weight = []
    for vehicle in petits_chevaux_list:
        s.append(vehicle[0])
        s_without_weight.append(vehicle[0][0])
    s = [s]

    #Keep track of the solutions that were already visited
    all_solutions = {}
    all_solutions[str(removeWeight(s[0]))] = 1

    #Compute the number of collisions for the first solution
    init_nb_coll = len(isAcceptable(s_without_weight))
    sol_with_collisions = [[0 , float("inf")] for x in range(init_nb_coll)]
    print init_nb_coll

    print "start"
    minimum_coll_nb = init_nb_coll
    iter = 0
    for sol in s:
        if iter < max_nb_iter:
            sol_without_weight = removeWeight(sol)

            problems = isAcceptable(sol_without_weight)
            weight = solutionWeight(sol)
            #print "Solution is " + str(sol_without_weight) + " with weight " + str(weight) +  " and problems " + str(problems)
            if len(problems) == 0:
                print "solution found"
                if weight < w:
                    w = weight
                    solu = sol
            elif weight < w:
                #print "extension"
                sons = createSons(sol, problems, petits_chevaux_list, all_solutions)
                s.extend(sons)

            #Store the best solution for the corresponding number of collisions
            id = len(problems)
            if id < init_nb_coll:
                if id < minimum_coll_nb:
                    minimum_coll_nb = id
                if weight < sol_with_collisions[id][1]:
                    sol_with_collisions[id][1] = weight
                    sol_with_collisions[id][0] = sol

            iter += 1
            #print iter

    return [solu, w, minimum_coll_nb, sol_with_collisions]



print petitsChevauxAlg(petitsChevauxList(200, 5, 400), 1e4)

#print isAcceptable([1, 5, 8, 4, 7, 5, 7, 9])