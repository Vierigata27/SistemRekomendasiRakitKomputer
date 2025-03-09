from sqlalchemy import create_engine
import pandas as pd
import random

# Konfigurasi koneksi database
DB_USERNAME = "root"
DB_PASSWORD = ""  # Kosong sesuai dengan konfigurasi
DB_HOST = "127.0.0.1"
DB_PORT = "3306"
DB_NAME = "skripsi"

# Membuat koneksi database
engine = create_engine(f"mysql+pymysql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

# Ambil data komponen dari database dengan JOIN ke tabel kategori
query = """
SELECT k.*, c.nama_kategori 
FROM komponen_komputer k
JOIN kategori c ON k.id_kategori = c.id_kategori
"""
komponen_df = pd.read_sql(query, engine)

class RekomendasiRakitan:
    def __init__(self, komponen_df, pop_size=200, generations=1000, budget=5000000):
        self.komponen_df = komponen_df
        self.pop_size = pop_size
        self.generations = generations
        self.budget = budget
        self.history = []

    def create_individual(self):
        return {
            'CPU': self.random_component(1),
            'Motherboard': self.random_component(2),
            'GPU': self.random_component(3),
            'RAM': self.random_component(4),
            'Storage': self.random_component(5),
            'Power Supply': self.random_component(6),
            'Casing': self.random_component(7),
            'Fan CPU': self.random_component(8),
        }

    def random_component(self, category_id):
        available_components = self.komponen_df[self.komponen_df['id_kategori'] == category_id]
        return available_components.sample().iloc[0].to_dict() if not available_components.empty else None

    def calculate_fitness(self, individual):
        total_harga = sum(comp['harga_komponen'] for comp in individual.values() if comp)
        total_performa = sum(comp['performa_komponen'] for comp in individual.values() if comp)
        compatibility = 1 if self.check_compatibility(individual) else 0

        if total_harga > self.budget:
            return 0
        
        return (total_performa * compatibility) / ((self.budget - total_harga) + 1)

    def check_compatibility(self, individual):
        return individual['CPU']['soket_komponen'] == individual['Motherboard']['soket_komponen'] if individual['CPU'] and individual['Motherboard'] else False

    def crossover(self, parent1, parent2, crossover_rate=0.5):
        """Melakukan crossover dengan probabilitas tertentu"""
        child = {}
        for key in parent1:
            if random.random() < crossover_rate:  # 40% kemungkinan terjadi crossover
                child[key] = parent2[key]
            else:
                child[key] = parent1[key]
        return child

    def mutate(self, individual, mutation_rate=0.5):
        if random.random() < mutation_rate:
            category_map = {
                "CPU": 1,
                "Motherboard": 2,
                "GPU": 3,
                "RAM": 4,
                "Storage": 5,
                "Power Supply": 6,
                "Casing": 7,
                "Fan CPU": 8,
            }
            category = random.choice(list(individual.keys()))
            if category in category_map:
                individual[category] = self.random_component(category_map[category])
        return individual

    def run_genetic_algorithm(self):
        """Menjalankan algoritma genetika"""
        population = [self.create_individual() for _ in range(self.pop_size)]
        best_overall_fitness = 0
        best_generation = 0
        best_overall_individual = None

        for generation in range(self.generations):
            population = sorted(population, key=lambda ind: self.calculate_fitness(ind), reverse=True)
            best_individual = population[0]
            best_fitness = self.calculate_fitness(best_individual)
            total_harga = sum(comp['harga_komponen'] for comp in best_individual.values() if comp)
            total_performa = sum(comp['performa_komponen'] for comp in best_individual.values() if comp)
            
            self.history.append({
                "Generasi": generation + 1,
                "Fitness": best_fitness,
                "Harga": total_harga,
                "Performa": total_performa
            })

            if best_fitness > best_overall_fitness:
                best_overall_fitness = best_fitness
                best_generation = generation + 1
                best_overall_individual = best_individual

            population = population[:self.pop_size // 2]
            new_population = [best_individual]  # Memastikan individu terbaik tetap ada
            for _ in range(self.pop_size - 1):  # Sisanya hasil crossover
                parent1, parent2 = random.sample(population, 2)
                child = self.crossover(parent1, parent2, crossover_rate=0.4)  # Crossover rate 40%
                child = self.mutate(child)
                new_population.append(child)

            population = new_population

        return best_overall_individual, best_overall_fitness, best_generation, pd.DataFrame(self.history)

# Jalankan algoritma genetika dengan data dari database
rekomendasi = RekomendasiRakitan(komponen_df)
best_rakitan, best_fitness, best_generation, history_df = rekomendasi.run_genetic_algorithm()

print("\nFitness Terbaik per Generasi:")
print(history_df.to_string(index=False))

print("\nGenerasi Terbaik: ", best_generation)
print("\nRakitan Terbaik:")
for key, value in best_rakitan.items():
    if value:
        print(f"{key}: {value['nama_komponen']} (Harga: {value['harga_komponen']}, Performa: {value['performa_komponen']})")

print(f"\nTotal Harga: {sum(comp['harga_komponen'] for comp in best_rakitan.values() if comp)}")
print(f"Total Performa: {sum(comp['performa_komponen'] for comp in best_rakitan.values() if comp)}")
print(f"Fitness Score: {best_fitness}")
