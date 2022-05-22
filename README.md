# OPTimization of Individual Mobility Schedules (OPTIMS)

``optims-sbb`` is a collaborative repository initiated by the
[Transport and Mobility Laboratory at EPFL](https://www.epfl.ch/labs/transp-or/)
and [Swiss Federal Railways (SBB)](https://www.sbb.ch/de).


## Functionality

``optims-sbb`` provides the functionality to solve the *activity-based schedule generation*-problem. It is based on
utility-maximizing principles and is able to simulate multiple choice dimensions simultaneously in a mixed-integer
linear program (MILP). The theoretical framework of the MILP was developed by `EPFL` ( `[1]`). `SBB` (`[2]`)
implemented the more generic software including a parallel computing solution as present in this repository. 
Also, they demonstrated the applicability on a larger scale including parameter estimation.

As an input, it requires an *activity set* per person as well as a *travel time matrix* for all possible combinations
between modes and origin-destination pairs. One activity in the activity set must consist of a type (e.g., leisure),
possible locations (football, climbing, dance), a preferred start time and duration, as well as a scoring group. The
scoring group refers to the *activity parameter*, which is the third required input.

Please note that this repository does not provide the functionality to estimate the activity parameter in
the utility specification nor the generation of the initial activity sets.


## Usage

Two fully operational scenarios are given under ``scripts``:

1) ``example``:  simulates a minimal example of a schedule generation for one person. It can be used to test new
   developments. The input data is available under ``assets/example``.
2) ``destination choice``: runs an example of an optimization model for one person with a choice set of 10 considered
   locations per activity. The input data is available under ``assets/destination_choice``.

If you use this repository for your own publication, please cite `[1]` and `[2]` from below.


## Collaboration

We are very happy to include any motivated collaborator. You are very welcome to integrate new functionality and new
scenarios into ``optims-sbb``.


## Literature

[1] Pougala, J., Hillel, T., and Bierlaire, M. (2022).
[Capturing trade-offs between daily scheduling choices.](https://www.sciencedirect.com/science/article/pii/S1755534522000124)
*Journal of choice modelling* 43, 100354.

[2] Manser, P., Haering, T., Hillel, T., Pougala, J., Krueger, R., and Bierlaire, M. (2021).
[Resolving temporal scheduling conflicts in activity-based modelling.](https://transp-or.epfl.ch/documents/technicalReports/ManserEtAl2021.pdf)
*Technical Report TRANSP-OR 211209*, Lausanne, Switzerland.

[3] Pougala, J., Hillel, T., and Bierlaire, M. (2021).
[Choice set generation for activity-based models.](http://www.strc.ch/2021/Pougala_EtAl.pdf)
In: *Swiss Transport Research Conference 2021*, Ascona, Switzerland.

-----

## Licensing

``optims-sbb`` is licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) for the full license text.

This license does not grant permission to use the trade names, trademarks, service marks, or names of the Licensors (SBB), 
except as required for reasonable and customary use in describing the origin of the work and reproducing the
content of the copyright notice.

