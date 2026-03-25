from dataclasses import dataclass


class GroundConnection:
    def __init__(
        self,
        sim_data: SimulationData,
        ):
        pass

    @property
    def distance(self) -> float:
        #TODO use existing line of sight function here
        return 0.0

    def _is_aligned(self) -> bool:
        pass

    def _is_too_far(self) -> bool:
        pass
    
    def _is_behind_horizon(self) -> bool:
        pass
    
    def _cloud_blocked(self) -> bool:
        pass
    
    def has_connection(self) -> bool:
        if self._is_aligned and not self._is_too_far and not self._is_behind_horizon and not self._cloud_blocked:
            return True
        return False
    
    
