# Nadex API client

Unofficial Nadex API client.
This code is alpha.

# REST API
- Login & Retrieve Account Information
- Market Search to Populate a Market Grid
- Place a Trade via Market Order
- Add Stop and/or Limit Order to an Open Trade
- Create an Entry Order
- Create a Watchlist
- Delete a Watchlist
- Quote Mode Trading
- Remove Existing Stop/Limit Order


| Category | Function | Method  | Implemented | Tested |
| -------- | -------- | ------- | ----------- | ------ |
| Account  | login    |  Account.login | Yes        | No     |
|          | balance  |  get_balance() | Yes        | No     |
| Order    | new      |  Order(**params) | No         | No     |
|          | list     |  Order.all() | No         | No     |
|          | get      |  Order.get(id) | No         | No     |
|          | update   |  order.update(**params) | No         | No     |
|          | cancel   |  Order.cancel(id) | No         | No     |
| Position | list     |  Position.all() | No         | No     |
|          | get      |  Position.get(id) | No         | No     |
| Market   | list     |  No         | No     |
| Instrument| list     |  No         | No     |
|          | get      |  No         | No     |
| Contract | list     |  No         | No     |
|          | get      |  No         | No     |
|          | update   |  No         | No     |
|          | cancel   |  No         | No     |
| Quote    | list     |  No         | No     |
|          | get      |  No         | No     |
|          | update   |  No         | No     |
|          | cancel   |  No         | No     |
| Epic     | list     |  No         | No     |
|          | get      |  No         | No     |
|          | update   |  No         | No     |
|          | cancel   |  No         | No     |


## Resources

| Name | Operation | HTTP Method | URL path |
| ---- | --------- | ----------- | -------- |
| Account | login | POST | v2/security/authenticate |
| Market | list | GET | markets/navigation |
| Epic   | get  | GET | markets/details |
| Order | list | GET | orders/workingorders |
|       | get  | GET | markets/details/workingorders |
|       | create | POST | dma/workingorders |
|       | cancel | DELETE | orders/workingorders/dma |
| Position | list | GET | orders/positions |
| Instrument | | | markets/navigation |
| Timeseries | | |markets/navigation |
| Contract |  | | markets/navigation |


Some resources share the same URL path.

# Streaming API

- Account Detail
- Signal Centre
- ERS events
- MGE events
- Heartbeat
- Hierarchical instrument ID
- Price Quote
- Market
