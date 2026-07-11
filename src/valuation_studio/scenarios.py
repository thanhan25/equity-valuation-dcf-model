"""Scenario management engine for handling Bull, Base, and Bear cases."""
from dataclasses import dataclass


@dataclass
class Scenario:
    name: str
    rev_growth: float
    ebitda_margin: float
    wacc: float
    terminal_growth: float


class ScenarioManager:
    """Provides standard institutional equity research scenario parameters."""
    @staticmethod
    def get_defaults() -> dict[str, Scenario]:
        return {
            "bull": Scenario(
                name="Bull Case",
                rev_growth=0.25,
                ebitda_margin=0.48,
                wacc=0.085,
                terminal_growth=0.035
            ),
            "base": Scenario(
                name="Base Case",
                rev_growth=0.18,
                ebitda_margin=0.42,
                wacc=0.095,
                terminal_growth=0.025
            ),
            "bear": Scenario(
                name="Bear Case",
                rev_growth=0.10,
                ebitda_margin=0.35,
                wacc=0.110,
                terminal_growth=0.015
            )
        }
