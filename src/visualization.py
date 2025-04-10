# src/visualization.py
import matplotlib.pyplot as plt
import logging

logger = logging.getLogger(__name__)

class Visualizer:
    def __init__(self, results_dir):
        self.results_dir = results_dir

    def plot_population_change(self, pop_change_data):
        """Generate a plot of population changes by state"""
        try:
            plt.figure(figsize=(10, 6))
            states = [row[0] for row in pop_change_data]
            changes = [row[1] for row in pop_change_data]
            plt.bar(states, changes)
            plt.xticks(rotation=45)
            plt.title('Top 10 States by Population Change')
            plt.xlabel('State')
            plt.ylabel('Population Change')
            plt.tight_layout()
            plt.savefig(f'{self.results_dir}/pop_change_plot.png')
            plt.close()
            logger.info("Population change plot saved successfully")
        except Exception as e:
            logger.error(f"Visualization failed: {e}")
            raise
