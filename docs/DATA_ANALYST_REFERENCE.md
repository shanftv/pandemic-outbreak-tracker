# data analyst

this doc covers everything data analyst put together for the Simple-Epidemic simulation integration.

---

## what was done

3 main modules to make the simulation data actually usable:

1. **parameter validation** - makes sure simulation configs aren't broken
2. **epidemic metrics** - calculates all the epidemic numbers (Rt, R0, CFR, etc.)
3. **data transformation** - converts simulation output into formats we can actually use
4. **schema definitions** - defines data structures for everything
5. **test coverage** - 49 tests to make sure it all works

---

## part 1: parameter validation

file: api/services/simulation_service.py

the simulation takes like 11 different parameters and they can't all be random values. built a validator that checks:

- population size must be 50-5000 (makes sense, can't simulate 10 billion people)
- grid size 10-500 (spatial area for agents)
- infection_rate, incubation_mean, infectious_mean (disease parameters)
- mortality_rate, vaccination_rate (intervention stuff)
- detection_probability, isolation_compliance (response behaviors)
- time_step (usually 0.1-1 day)
- initial_infected (at least 1 person)

also checks that all these make sense together (like initial_infected can't be bigger than population_size, and total simulation time can't exceed 365 days).

example usage:
```python
from api.services.simulation_service import SimulationService

service = SimulationService()
is_valid, error_msg = service.validate_simulation_config(config)
if is_valid:
    print("looks good to go")
else:
    print(f"problem: {error_msg}")
```

---

## part 2: epidemic metrics

file: api/services/stats_utils.py (about 350 lines)

here's where the actual calculations happen. built 11 different metrics:

| metric | what it measures | uses | notes |
|--------|-----------------|------|-------|
| Rt | reproduction number right now | last 7 days of data | if > 1 virus spreading, < 1 slowing down |
| R0 | how contagious initially | first 10% of outbreak | same interpretation as Rt |
| attack rate | what % of people got sick | whole outbreak | 0-100% |
| CFR | what % of infected died | whole outbreak | case fatality rate |
| doubling time | how fast cases double | growth phase | lower is faster spread |
| growth rate | recent growth speed | last few days | percent per day |
| peak metrics | when did it peak + how many | whole outbreak | max infections + which day |
| epidemic duration | how many days had cases | whole outbreak | days count |
| trend | is it going up/down/flat | last week | basically slope |

i used exponential growth model for this stuff:
```
I(t) = I₀ × exp(λt)
Rt = 1 + λ × infectious_period
```

means if you know the growth rate (λ), you can figure out how many people each infected person infects on average.

using the metrics:
```python
from api.services.stats_utils import EpidemicStats

infected_counts = [1, 2, 4, 8, 16, 32, 64]
rt = EpidemicStats.calculate_rt(infected_counts, infectious_period=7)
r0 = EpidemicStats.estimate_r0(infected_counts, infectious_period=7, population=1000)
cfr = EpidemicStats.calculate_case_fatality_rate(total_infected=100, deaths=2)
trend = EpidemicStats.calculate_trend(rt_values)
```

---

## part 3: data transformation

file: api/services/data_transform.py (about 380 lines)

simulation spits out agent positions and SEIRD counts, but that's not very useful on its own. i built transformers to convert it into:

| what it does | output format | why |
|--------------|---------------|-----|
| agents_to_geojson | GeoJSON | can visualize on a map |
| create_seird_pivot_table | CSV-ready table | easier to analyze |
| calculate_risk_score | 0-100 number | quick risk indicator |
| export_to_json | JSON file | store the results |
| export_to_csv | CSV file | import to excel/pandas |
| create_danger_zone_geojson | GeoJSON with risk coloring | map the risky areas |

risk score is basically a weighted average of:
- infected percentage (30%)
- growth rate (30%)
- Rt value (20%)
- doubling time (20%)

so if cases are growing fast, lots of people infected, AND Rt is high, the score goes up to like 80-100.

example:
```python
from api.services.data_transform import SimulationTransformer

# convert agent positions to map data
geojson = SimulationTransformer.agents_to_geojson(agents, location_id="ncr")

# calculate how risky a location is
risk = SimulationTransformer.calculate_risk_score(infected_pct=20, growth_rate=0.1, rt=1.5, doubling_time=4)

# save to file
SimulationTransformer.export_seird_to_csv(statistics, "output.csv")
```

---

## part 4: schema definitions

file: api/models/schemas.py (added about 100 lines)

defined these data structures so everything has consistent types:

- SimulationConfig: what you send in (all the parameters)
- SimulationStatistics: the raw SEIRD numbers over time
- EpidemicMetrics: the calculated metrics (Rt, R0, etc.)
- AgentData: where each agent is + their state
- SimulationOutput: complete response from simulation

pydantic validates all of it automatically, so if someone sends bad data, it fails with a clear error message.

---

## part 5: testing

file: tests/test_simulation_integration.py (650+ lines)

wrote 49 tests to make sure nothing breaks:

**parameter validation tests (16 tests):**
- tested min/max boundaries (50 people minimum, 5000 max)
- tested with zero mortality, 100% mortality
- tested invalid combinations (negative values, backwards time)
- tested edge cases (1 person infected, population of 50)

**metrics tests (20 tests):**
- Rt with different infection patterns (stable, growing, declining)
- R0 accuracy
- doubling time calculations
- attack rate at 0% and 100%
- CFR edge cases
- trend detection
- peak finding

**transformation tests (13 tests):**
- single agent to GeoJSON
- multiple agents to GeoJSON
- empty data (no agents)
- risk score boundaries (0 and 100)
- pivot table creation
- danger zone classification

all 49 tests pass. ran them like 50 times during development.

run tests yourself:
```bash
# everything
pytest tests/test_simulation_integration.py -v

# just one test class
pytest tests/test_simulation_integration.py::TestEpidemicMetricsCalculation -v

# with coverage report
pytest tests/test_simulation_integration.py --cov=api.services
```

---

## parameter reference

values that need to stay in bounds:

| parameter | min | max | what is it |
|-----------|-----|-----|-----------|
| population_size | 50 | 5000 | how many agents |
| grid_size | 10 | 500 | map area |
| infection_rate | 0 | 10 | how contagious |
| incubation_mean | > 0 | - | days exposed before sick |
| infectious_mean | > 0 | - | days contagious |
| mortality_rate | 0 | 1 | fraction who die |
| vaccination_rate | 0 | 1 | daily vaccination |
| detection_probability | 0 | 1 | chance of finding infected |
| isolation_compliance | 0 | 1 | how many actually isolate |
| time_step | > 0 | 1 | simulation step size |
| initial_infected | 1 | population_size | starting infected count |

---

## the math stuff

just in case you need the formulas:

**Rt (how many people get infected)**
```
I(t) = I₀ × e^(λt)
Rt = 1 + λ × infectious_days

if Rt > 1 → outbreak spreading
if Rt < 1 → outbreak dying out
```

**R0 (initial contagiousness)**
basically same as Rt but measured at the very start when there's no immunity yet.

**attack rate**
```
% = (total_who_got_sick / population) × 100
```

**case fatality rate**
```
% = (deaths / total_infected) × 100
```

**doubling time**
how many days until cases double. calculated from λ.

**risk score**
```
score = 30% of infected% + 30% of growth_rate + 20% of Rt + 20% of doubling
result is 0-100
```

---

## quick stats

what i actually built:

| part | file | lines | classes | methods |
|------|------|-------|---------|---------|
| validation | simulation_service.py | 430 | 1 | 8 |
| metrics | stats_utils.py | 350 | 1 | 11 |
| transformation | data_transform.py | 380 | 1 | 10 |
| tests | test_simulation_integration.py | 650 | 3 classes | 49 tests |
| schemas | schemas.py | +100 | - | 5 added |

around 1,160 lines of actual code, 650+ lines of tests.