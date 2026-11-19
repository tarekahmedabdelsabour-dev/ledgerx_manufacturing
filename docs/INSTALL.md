# Install

```
cd ~/frappe-bench-v16/apps
git clone <repo-url> ledgerx_manufacturing
cd ~/frappe-bench-v16
printf '\nledgerx_manufacturing\n' >> sites/apps.txt
./env/bin/pip install -e apps/ledgerx_manufacturing
ln -sfn ~/frappe-bench-v16/apps/ledgerx_manufacturing/ledgerx_manufacturing/public sites/assets/ledgerx_manufacturing
bench --site mysite.localhost install-app ledgerx_manufacturing
bench --site mysite.localhost migrate
bench --site mysite.localhost clear-cache
```

Then a full restart. If the server answers 000, a step above was skipped (clone, apps.txt line or pip install).

Update later: `cd apps/ledgerx_manufacturing && git pull origin main`, then migrate, clear-cache and restart.

## After install

1. Open **Factory Settings** and choose the rules you want.
2. Create **Production Lines** and set the Production Line on each Workstation.
3. Print labels: Workstation, Employee and Job Card forms have Barcode -> Print Barcode Label.
4. Open `/factory` on the shop-floor phone or scanner PC.
