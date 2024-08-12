from fastapi import FastAPI, HTTPException
from typing import List
from fastapi.middleware.cors import CORSMiddleware
import re

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Data provided in the paste
data = """Artist   Amount
0                              AMOXD   0.1354
1                             Almkit   0.0071
2                             Bassid   0.0298
3                          Big Power   1.3226
4                            Black H   5.5538
5                 Bricefa La légende   0.1108
6                         DJÔDJÔRÔBÔ   0.1805
7                         DNL Kazama   0.1627
8                            Dembouz   0.1275
9                  Deuspi the rapper   2.1932
10                   Dim's crescendo   0.4445
11             Dixrock, Ashley Power   0.0626
12                            Djeezy   0.8689
13                   Djeezy, Toza, N   0.2423
14                        Djoblack'b   2.3395
15                  EMSO 225, Wesley   0.2570
16                            H'Lams   1.0692
17                               H.A   0.0539
18                           Halim C   3.4078
19                   Huguo Boss, DDK   2.3618
20                             J.C.B   1.3931
21                         Johnny lp   0.2832
22                    KSD, FK Leader   0.9853
23                              Kara   0.1797
24                          Kaza 225   0.0155
25                     Le Chouchouté   5.9840
26                       Lyon Spirit   0.0769
27                       Léo Lil Boy   0.0408
28                        MC Bugarri   0.2695
29                                MS   1.8603
30                          Max e'sh   0.0111
31          Memphis Killah, Dam Tito   0.0282
32                              Mozo   1.2683
33                      ND2B, SHVDOW   0.1165
34                              NIVA   0.0534
35                      Obman BigBoy   0.0715
36                        Prezy Gvng   0.2522
37                     Ratio Positif   0.0003
38                       Regis SOSSA   1.7276
39              Regis SOSSA, Dembouz  28.6882
40                          Rh Rahim   0.0426
41                            Shisco   0.2311
42                             Smalt   0.0492
43                          THE LORD  13.7254
44  THE LORD, Darki, Odia The Meanie   8.1032
45             THE LORD, Hot Hearted   3.9835
46                    Thug six16teen   3.9018
47                           Tshevan   1.6821
48                           Zabrota   0.0132"""

# Process the data
lines = data.strip().split('\n')[1:]  # Skip the header
artist_data = {}

for line in lines:
    parts = line.split()
    amount = float(parts[-1])
    artist = ' '.join(parts[1:-1])
    artist_data[artist] = amount

def get_recommendations(artist_name: str, n: int = 3) -> List[str]:
    if artist_name not in artist_data:
        raise HTTPException(status_code=404, detail="Artist not found")
    
    artist_amount = artist_data[artist_name]
    
    # Calculate the difference in streaming numbers
    differences = {}
    for artist, amount in artist_data.items():
        if artist != artist_name:
            diff = abs(amount - artist_amount)
            # Check if the input artist name is part of this artist name
            if artist_name in artist:
                # Remove the input artist name and any leading/trailing commas and spaces
                remaining = re.sub(f'^{re.escape(artist_name)},?\s*|,?\s*{re.escape(artist_name)}$', '', artist).strip(', ')
                if remaining:  # Only add if there's something left after removal
                    differences[remaining] = diff
            else:
                differences[artist] = diff
    
    # Sort by the smallest difference
    sorted_artists = sorted(differences, key=differences.get)
    
    return sorted_artists[:n]

@app.get("/recommendation/")
async def recommend(artist_name: str):
    try:
        recommendations = get_recommendations(artist_name)
        return {"artist": artist_name, "recommendations": recommendations}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)