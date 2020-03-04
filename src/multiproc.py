import ray
import time
import numpy as np
import scipy as sp
from src.build import *
from src.proyection import proyect_into_linear
#from examples.ex3x3gen import g, N, T


@ray.remote
class Agent(object):
    
    def __init__(self, n, game):

        C, b, ma = build_proyection_player(n, game)
        T = game.T
        N = game.N
        self.n = n
        self.C = C
        self.b = b
        self.ma = ma
        self.N = game.N
        self.T = game.T
        self.alpha = game.alpha
        self.neighbors = list(game.G.neighbors(n))
        self.ws = np.zeros(4 * T * N + 2 * T)
        self.xs = np.zeros(4 * T * N + 2 * T)

        pl = game._player_list[n]
        self.grad = np.hstack([
            np.ones(T) * pl._sm - pl._s0,
            np.ones(T) * pl._s0,
            np.ones(2 * T) * pl._ram,
            np.ones(T) * pl._x,
            np.ones(T) * (- pl._x),
        ])
        
    def update(self, xs):
        tmp = self.xs.copy()
        tmp[self.ma] -= self.alpha * self.grad
        tmp -= self.alpha * self.ws
        #for n_ in range(self.N):
        for n_ in self.neighbors:
            #if n_ != self.n:
            tmp -= self.alpha * (self.xs - xs[n_])

        new_x = tmp.copy()
        sol = proyect_into_linear(tmp[self.ma], self.C, self.b)
        new_x[self.ma] = sol[0]

        dis = np.linalg.norm(new_x - self.xs)
        self.xs = new_x

        return self.xs, dis

    def update_w(self, xs):
        n = self.n 
        for n_ in self.neighbors:
        #for n_ in range(N):
            #if n != n_:
            self.ws += self.xs - xs[n_]

    #def update_old(self, xs_old, xs_new):
    #    xs_old[self.n] = xs_new[self.n]

    def print_cost(self):
        return np.inner(self.xs[self.ma], self.grad)

    def print_neighbors(self):
        print(self,n, self.neighbors)
         

def run_distributed(game, max_iters=15000, tol=1e-7):

    ray.init(
        include_webui=False,
#        memory=4000 * 1024 * 1024,
#        object_store_memory=4000 * 1024 * 1024,
#        driver_object_store_memory=100 * 1024 * 1024)
    )

    N = game.N
    T = game.T
    n_vars = 4 * T * N + 2 * T

    agents = []
    for n in range(N):
        ag = Agent.remote(n, game)
        agents.append(ag)

    xs = [np.zeros(n_vars) for _ in range(N)]
    xs_id = ray.put(xs)

    iteration_times = np.zeros(max_iters)

    #iteration_data = []

    for i in range(max_iters):
        start = time.time()    
        fut = [ag.update.remote(xs_id) for ag in agents]
        xs_id = ray.get(fut)

        xs_id, dist = zip(*xs_id)

        mdis = max(dist)
        if mdis < 1e-8:
            break


        #preserve = np.vstack(xs_id).copy()
        #preserve = sp.sparse.csc_matrix(preserve)
        #iteration_data.append(preserve)
        
        #if i % 50 == 0:
        #    if np.allclose(0,
        #        np.diff(np.vstack(xs_id).reshape(N, -1), axis=0),
        #        atol=tol):
        #        break
        #xs_id = ray.put(fut)
        fut2 = [ag.update_w.remote(xs_id) for ag in agents]
        _ = ray.get(fut2)
        iteration_times[i] = time.time() - start


    final_costs = ray.get([ag.print_cost.remote() for ag in agents])        

    ray.shutdown()

    return final_costs, iteration_times, i


if __name__ == '__main__':

    ## 20, 24, complete -> 1137 s
    ## 20, 10, complete -> 80s
    
    
    from src.game import generate_random_uniform
    g = generate_random_uniform(20, 10, 'complete', 6789)
    g.init()
    
    start = time.time()
    s = run_distributed(g)
    end = time.time()
    s_ = s[0]
    pc = g.get_payoff_core()
    dis = np.linalg.norm(s_ - pc)
    elap = end - start
    print('Distnace', dis.round(5), 'Time', round(elap, 5), 'Iterations', s[2])

    
