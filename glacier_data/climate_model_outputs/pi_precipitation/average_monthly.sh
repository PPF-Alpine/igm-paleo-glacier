# Average each month separately, then combine
for mon in {01..12}; do
    cdo selmon,$mon -selyear,1960/2014 pr_historical_250years.nc pr_mon${mon}_temp.nc
    cdo timmean pr_mon${mon}_temp.nc pr_mon${mon}_mean.nc
    rm pr_mon${mon}_temp.nc
done
cdo mergetime pr_mon??_mean.nc pr_manual_ymonmean.nc
rm pr_mon??_mean.nc
