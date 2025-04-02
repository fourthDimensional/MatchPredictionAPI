from pydantic import BaseModel, Field

class Team(BaseModel):
    number: int = Field(..., ge=0, le=99999)
    name: str = Field(..., regex=r'frc\d+')
    metadata: dict = Field({}, description='Additional metadata about the team')

class Match(BaseModel):
    key: str = Field(..., regex=r'\d{4}[a-z0-9]+_[a-z0-9]+') # e.g., 2025mibig_qm45
    winning_alliance: str = Field(..., regex=r'red|blue')
    alliances: dict = Field(..., description='Alliance data for the match')
    score_breakdown: dict = Field(..., description='Detailed score breakdown for the match')