

class ResultsWriter:
    def write_average_durations(self, results):
        with open("results/results_average_durations.txt", "w") as file:
            file.write(f"La duración promedio de viajes que"
                       f" iniciaron en días con precipitaciones mayores a 30mm.\n")
            file.write(f"Cantidad de fechas: {len(results)}\n")
            file.write(f"Fecha - Promedio\n")
            for date, average in results:
                file.write(f"{date} - {average}\n")

    def write_trips_per_year(self, results):
        with open("results/results_trips_per_year.txt", "w") as file:
            file.write(f"Los nombres de las estaciones que al menos"
                       f" duplicaron la cantidad de viajes iniciados en"
                       f"ellas entre 2016 y el 2017.\n")
            n_stations = sum([len(city_data[1]) for city_data in results])
            file.write(f"Cantidad de estaciones: {n_stations}\n")
            for city_data in results:
                file.write(f"Ciudad: {city_data[0]}\n")
                file.write(f"Estacion - Cantidad en 2016 - Cantidad en 2017\n")
                for station, first_year_compare, second_year_compare in city_data[1]:
                    file.write(f"{station} - {first_year_compare} - {second_year_compare}\n")


    def write_average_distances(self, results):
        with open("results/results_average_distance.txt", "w") as file:
            file.write(f"Los nombres de estaciones de Montreal para la que el promedio"
                       f" de los ciclistas recorren más"
                       f"de 6km en llegar a ellas.\n")
            file.write(f"Cantidad de estaciones: {len(results)}\n")
            file.write(f"Estacion - Distancia Promedio\n")
            for station, average_distance in results:
                file.write(f"{station} - {average_distance}\n")
