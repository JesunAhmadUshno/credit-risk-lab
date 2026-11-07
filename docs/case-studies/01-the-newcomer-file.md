# Case study 1: The newcomer file

*A thin-file applicant walks through the lab's machinery. Every number
is from results/study.json and results/second_look.json; the applicant
is a composite, the arithmetic is real.*

## The applicant

She landed in Toronto fourteen months ago with a professional job, a
bank account, and no Canadian credit history. Her file, in the sense a
bureau means it, is nearly empty: no tradelines with history, no score
worth the name. She applies for a card to start building one.

A scorecard that keys on file depth sees the emptiness, not the
person. In this lab's terms she is the thin-file problem from
RESEARCH.md: creditworthy and credit-invisible are the same silhouette
to a model that cannot observe behaviour.

## What the lab measured

The fair access study (src/study.py) retrained the champion model with
every bureau-style field removed - no credit limit, no age, no
demographics, no bill or payment amounts - keeping only behavioural
features and the payment history itself: utilization, payment ratio,
delinquency mean and maximum, bill trend, months past due, and the
six-month payment-status path.

- Thin-file AUC: **0.7687**
- Full model AUC: **0.7810**
- Gap: **-0.0123**, with a bootstrap 95% CI on the thin-file AUC in
  results/rigor.json

Behavioural evidence carries nearly all of the signal. A person with
fourteen months of observable payment behaviour is not a blank file;
she is a file written in a different column.

The same study priced the standard cut-off. Set to hold the approved
book at the Stage 1 default rate (12.44%), the cut-off approved 6,614
of 9,000 test applicants and rejected 2,386. Of the rejected, **1,218
(51.0%) did not default**: the creditworthy rejects. Any applicant pool
with newcomers in it concentrates exactly there, because thin files
score cautiously even when the person pays.

## The second look

The Second-Look Recovery Policy (pre-registered as H1) gives the
rejected a second score instead of a final answer: if a reject's
thin-file behavioural PD is at or below the median behavioural PD of
approved applicants (band: 0.1170), the behavioural evidence is at
least as strong as the typical approved applicant's, and the
application is approved on second look.

Measured on the test set, that strict band is nearly empty: it
recovered **13 of the 2,386 rejects - 10 creditworthy applicants
(0.8% of all creditworthy rejects) and 3 defaults** - moving the
approved book's default rate from 12.44% to 12.46% (+0.02 percentage
points). H1 was REFUTED on its recovery bound, and the refutation is
the useful part: behavioural scores and champion scores move
together, so almost nobody the champion refuses carries
approved-median behavioural evidence. Our composite applicant, paying
in full at moderate utilization, is exactly the profile the band was
built for - and the measurement says profiles like hers are rare
among rejects, not common. A policy that assumes otherwise would be
recovering a rounding error at scale.

## What a lender could responsibly do

1. Score behaviour where behaviour exists. Rent, utilities, and
   account cash flow are observable for newcomers in ways bureau
   history is not; the thin-file result says that channel is worth
   most of a full model's discrimination.
2. Start small and graduate. A low-limit product converts an
   unobservable applicant into an observable one within months, at
   bounded exposure: the staging machinery in this lab is how that
   book gets watched.
3. Build the second look into the policy, with the band set by
   appetite and the price printed. The lab's strictest band costs
   almost nothing because it recovers almost nothing; a working
   policy chooses its band from a measured recovery-versus-cost
   curve (the follow-up experiment H1 defines), not from the hope
   that the rejected pool is full of hidden prime borrowers. This
   dataset says it is not.
4. Audit the outcome by group, with sizes printed. The study's
   fairness table is the template; on this data the widest gap sits
   in EDUCATION (29.2 points between the smallest and largest groups),
   which is what an audit is for: finding where the aggregate hides
   the injury.

The dataset behind these numbers is Taiwan, 2005, not Canada, and the
study says so on its own page. The applicant is a composite. The
method (measure the rejects, score the behaviour, price the recovery)
is the part that travels.
