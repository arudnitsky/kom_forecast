import csv
from dataclasses import dataclass
from typing import List

@dataclass
class KOMSegment:
    segment_name: str
    distance: str
    climb: str
    direction: str
    kom_holder: str
    kom_time: str
    speed: str
    my_rank: str
    my_time: str
    my_speed: str

    def get_direction_degrees(self) -> int:
        """Convert cardinal direction to degrees"""
        direction_to_degrees = {
            'N': 0, 'NNE': 22.5, 'NE': 45, 'ENE': 67.5,
            'E': 90, 'ESE': 112.5, 'SE': 135, 'SSE': 157.5,
            'S': 180, 'SSW': 202.5, 'SW': 225, 'WSW': 247.5,
            'W': 270, 'WNW': 292.5, 'NW': 315, 'NNW': 337.5
        }
        return direction_to_degrees.get(self.direction.strip(), 0)

def read_kom_list(filepath: str = 'kom-list.csv') -> List[KOMSegment]:
    """
    Read and parse the KOM list CSV file.
    
    Args:
        filepath: Path to the CSV file (default: 'kom-list.csv')
        
    Returns:
        List of KOMSegment objects containing the parsed data
    """
    segments = []
    
    with open(filepath, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            segment = KOMSegment(
                segment_name=row['Segment name'],
                distance=row['Distance'],
                climb=row['Climb'],
                direction=row['Direction'],
                kom_holder=row['KOM holder'],
                kom_time=row['KOM Time'],
                speed=row['Speed'],
                my_rank=row['My Rank'],
                my_time=row['My Time'],
                my_speed=row['My Speed']
            )
            segments.append(segment)
    
    return segments

# Example usage
if __name__ == "__main__":
    segments = read_kom_list()
    for segment in segments:
        print(f"\nSegment: {segment.segment_name}")
        print(f"Distance: {segment.distance}")
        print(f"KOM Holder: {segment.kom_holder}")
        print(f"KOM Time: {segment.kom_time}")
        print("-" * 50)