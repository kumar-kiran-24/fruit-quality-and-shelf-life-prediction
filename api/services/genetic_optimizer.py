import random
from typing import List, Dict, Any


class GeneticOptimizer:

    """
    Genetic Algorithm for batch-to-destination allocation.

    The optimizer tries to minimize:

    - travel distance
    - travel duration
    - shelf-life risk
    - destination capacity violations

    while maximizing:

    - destination suitability
    - available capacity
    """

    def __init__(
        self,
        population_size: int = 50,
        generations: int = 100,
        mutation_rate: float = 0.10,
        crossover_rate: float = 0.80
    ):

        self.population_size = population_size

        self.generations = generations

        self.mutation_rate = mutation_rate

        self.crossover_rate = crossover_rate

    # ========================================================
    # INITIAL POPULATION
    # ========================================================

    def create_population(
        self,
        batches: List[Dict[str, Any]],
        destinations: List[Dict[str, Any]]
    ):

        population = []

        destination_count = len(destinations)

        if destination_count == 0:
            return population

        for _ in range(self.population_size):

            chromosome = []

            for _batch in batches:

                destination_index = random.randint(
                    0,
                    destination_count - 1
                )

                chromosome.append(
                    destination_index
                )

            population.append(chromosome)

        return population

    # ========================================================
    # SHELF LIFE RISK
    # ========================================================

    def shelf_life_risk(
        self,
        shelf_life: str
    ) -> float:

        shelf_life = shelf_life.lower().strip()

        if "1-5" in shelf_life:
            return 1.0

        if "5-10" in shelf_life:
            return 0.6

        if "10-14" in shelf_life:
            return 0.2

        return 0.5

    # ========================================================
    # FITNESS FUNCTION
    # ========================================================

    def calculate_fitness(
        self,
        chromosome: List[int],
        batches: List[Dict[str, Any]],
        destinations: List[Dict[str, Any]]
    ):

        total_cost = 0.0

        used_capacity = {}

        for destination in destinations:

            used_capacity[
                destination["destination_id"]
            ] = 0.0

        for batch_index, destination_index in enumerate(
            chromosome
        ):

            batch = batches[batch_index]

            destination = destinations[
                destination_index
            ]

            # ------------------------------------------------
            # Distance
            # ------------------------------------------------

            distance = batch.get(
                "distances",
                {}
            ).get(
                destination["destination_id"],
                0
            )

            # ------------------------------------------------
            # Duration
            # ------------------------------------------------

            duration = batch.get(
                "durations",
                {}
            ).get(
                destination["destination_id"],
                0
            )

            # ------------------------------------------------
            # Shelf-life risk
            # ------------------------------------------------

            shelf_risk = self.shelf_life_risk(
                batch.get(
                    "shelf_life_prediction",
                    ""
                )
            )

            # ------------------------------------------------
            # Capacity
            # ------------------------------------------------

            batch_quantity = batch.get(
                "quantity_kg",
                1
            )

            destination_id = destination[
                "destination_id"
            ]

            used_capacity[
                destination_id
            ] += batch_quantity

            available_capacity = destination.get(
                "available_capacity_kg",
                0
            )

            capacity_penalty = 0

            if (
                used_capacity[destination_id]
                > available_capacity
            ):

                excess = (
                    used_capacity[destination_id]
                    - available_capacity
                )

                capacity_penalty = (
                    excess * 100
                )

            # ------------------------------------------------
            # Fruit compatibility
            # ------------------------------------------------

            accepted_fruit = (
                destination
                .get("accepted_fruit", "")
                .lower()
            )

            fruit = (
                batch
                .get("fruit", "")
                .lower()
            )

            compatibility_penalty = 0

            if accepted_fruit != fruit:

                compatibility_penalty = 10000

            # ------------------------------------------------
            # Cost
            # ------------------------------------------------

            cost = (

                distance * 0.35

                + duration * 0.30

                + shelf_risk * 100 * 0.20

                + capacity_penalty * 0.10

                + compatibility_penalty * 0.05
            )

            total_cost += cost

        return total_cost

    # ========================================================
    # SELECTION
    # ========================================================

    def selection(
        self,
        population,
        batches,
        destinations
    ):

        ranked = sorted(
            population,
            key=lambda chromosome:
            self.calculate_fitness(
                chromosome,
                batches,
                destinations
            )
        )

        elite_count = max(
            2,
            int(
                len(ranked) * 0.20
            )
        )

        return ranked[:elite_count]

    # ========================================================
    # CROSSOVER
    # ========================================================

    def crossover(
        self,
        parent1,
        parent2
    ):

        if len(parent1) <= 1:

            return parent1.copy()

        if random.random() > self.crossover_rate:

            return parent1.copy()

        point = random.randint(
            1,
            len(parent1) - 1
        )

        child = (
            parent1[:point]
            +
            parent2[point:]
        )

        return child

    # ========================================================
    # MUTATION
    # ========================================================

    def mutate(
        self,
        chromosome,
        destination_count
    ):

        mutated = chromosome.copy()

        for index in range(
            len(mutated)
        ):

            if random.random() < self.mutation_rate:

                mutated[index] = random.randint(
                    0,
                    destination_count - 1
                )

        return mutated

    # ========================================================
    # RUN OPTIMIZATION
    # ========================================================

    def optimize(
        self,
        batches: List[Dict[str, Any]],
        destinations: List[Dict[str, Any]]
    ):

        if not batches:

            raise ValueError(
                "No batches supplied for optimization."
            )

        if not destinations:

            raise ValueError(
                "No destinations supplied for optimization."
            )

        population = self.create_population(
            batches,
            destinations
        )

        best_solution = None

        best_fitness = float("inf")

        for _generation in range(
            self.generations
        ):

            # ------------------------------------------------
            # Evaluate population
            # ------------------------------------------------

            for chromosome in population:

                fitness = self.calculate_fitness(
                    chromosome,
                    batches,
                    destinations
                )

                if fitness < best_fitness:

                    best_fitness = fitness

                    best_solution = chromosome.copy()

            # ------------------------------------------------
            # Selection
            # ------------------------------------------------

            parents = self.selection(
                population,
                batches,
                destinations
            )

            # ------------------------------------------------
            # New population
            # ------------------------------------------------

            new_population = [
                parent.copy()
                for parent in parents
            ]

            while len(new_population) < self.population_size:

                parent1 = random.choice(
                    parents
                )

                parent2 = random.choice(
                    parents
                )

                child = self.crossover(
                    parent1,
                    parent2
                )

                child = self.mutate(
                    child,
                    len(destinations)
                )

                new_population.append(
                    child
                )

            population = new_population

        if best_solution is None:

            raise ValueError(
                "Genetic Algorithm failed to produce a solution."
            )

        return (
            best_solution,
            best_fitness
        )