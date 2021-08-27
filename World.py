# World class: a collection of weather stations.

import pandas as pd
import matplotlib.pyplot as plt
import Constants
import time
import Utils


class World:


    def __init__(self):
        self.all_data = None
        self.data_type = None
        self.monthly_average = None
        self.monthly_count = None
        self.code = None

    def get_monthly_average(self, code=None, year_range=Constants.YEAR_RANGE, min_coverage=1, full_range=False, verbose=False):
        # Get average of all stations for every year and month.
        # min_coverage: minimum number of stations for a year to be included.

        self.code = code
        monthly_average = pd.DataFrame(columns=['Year'] + Constants.MONTHS)
        monthly_count = monthly_average.iloc[:, 0:2]
        monthly_count.columns = ['Year', 'Count']

        if code is None:
            df = self.all_data
        else:
            # Calculate each code's mean, then average all codes.
            # We use each code's mean independently to avoid bias coming from differences in coverage
            # in one code over time, giving it more influence on the total mean.
            if type(code) is tuple:
                # Average across multiple codes.
                all_codes_data = pd.concat([self.get_monthly_average(code=c, year_range=year_range, verbose=verbose)[0] for c in code])
                by_year = all_codes_data.groupby('Year', as_index=False)
                monthly_average = by_year.mean()
                # Use only years for which all codes have data.
                monthly_average = monthly_average.loc[by_year.count().iloc[:, 1] == len(code)]

                self.monthly_average = monthly_average
                self.monthly_count = None
                self.code = code
                return self.monthly_average, self.monthly_count

            df = self.all_data.loc[self.all_data.Name.str.startswith(code)]

        # Include only years with values for all months.
        df = df.dropna()

        if full_range:
            print('Selecting stations with full data range ... ', end='')
            start_time = time.time()

            # Include only stations that have data for all years in range.
            station_dict = {}
            name_year = df.loc[:, ['Name', 'Year']]
            for i in range(name_year.shape[0]):
                if name_year.Year.iloc[i] not in range(year_range[0], year_range[1]+1):
                    continue
                if name_year.Name.iloc[i] in station_dict.keys():
                    station_dict[name_year.Name.iloc[i]] += 1
                else:
                    station_dict[name_year.Name.iloc[i]] = 1
            stations = []
            for station_candidate in station_dict.keys():
                if station_dict[station_candidate] == year_range[1]-year_range[0]+1:
                    stations.append(station_candidate)
            df = df.loc[df.Name.isin(stations)]
            print('found %d stations in %s seconds' % (len(stations), str(round(time.time()-start_time, 2))))

            by_year = df.groupby('Year', as_index=False)
            monthly_average = by_year.mean()

            # Use only years for which all codes have the desired coverage.
            monthly_average = monthly_average.loc[by_year.count().iloc[:, 1] >= min_coverage]

            # Restrict years to required range.
            count =  by_year.count()
            count = count.loc[(count.Year >= year_range[0]) & (count.Year <= year_range[1])]
            monthly_average = monthly_average.loc[(monthly_average.Year >= year_range[0]) & (monthly_average.Year <= year_range[1])]

            for year in monthly_average.Year.to_list():
                if verbose and (not full_range):
                    print(str(year) + ", " + code + ", " + str(count.loc[count.Year == year].iloc[0, 1]) + " stations")

        self.monthly_average = monthly_average
        self.monthly_count = monthly_count
        return monthly_average, monthly_count

    def load_global_averages(self, filename, data_type):
        # Load pre-calculated global averages from csv.
        self.monthly_average = pd.read_csv(filename)
        self.data_type = Constants.DATA_TYPES[data_type]

    def plot_data(self, mode):
        # Plot global data.

        if self.monthly_average is None:
            raise(AttributeError, 'Please calculate global averages before plotting.')

        if self.monthly_average.shape[0] == 0:
            raise(ValueError('Monthly average data empty!'))

        mode = mode.upper()

        plt.figure()

        if mode in Constants.MONTHS:
            # Plot by year for a specific month.
            x_axis = self.monthly_average.Year
            y_axis = self.monthly_average[mode]
            plt.scatter(x_axis, y_axis, marker='.')
            plt.plot(x_axis, y_axis)

        elif mode == 'OVERLAY':
            # Plots by year for all month on the same figure.
            x_axis = self.monthly_average.Year
            [plt.plot(x_axis, self.monthly_average[m], linestyle='-', marker='o', markersize=6, color='b', label=m) for m in Constants.MONTHS]
            plt.legend()

        elif mode == 'ANNUAL':
            y_axis = []
            for y in self.monthly_average.Year:
                y_axis.append(Utils.get_annual_average(self.monthly_average[self.monthly_average.Year == y][Constants.MONTHS].values.tolist()[0], y))
            plt.scatter(self.monthly_average.Year, y_axis, marker='.')
            plt.plot(self.monthly_average.Year, y_axis)

        title_str = Constants.DATA_DESC[self.data_type]
        if self.code is not None:
            if type(self.code) is tuple:
                title_str += ('\nCode: ' + ' '.join(self.code))
            else:
                title_str += ('   |   Code: ' + self.code)
        plt.suptitle(title_str)
        plt.show()

    def load_data(self, source):

        # All data from: ftp://ftp.ncdc.noaa.gov/pub/data/ghcn/v4
        if source in ['GHCN_QCU', 'GHCN_QCF', 'GHCN_QFE']:
            # Quality controlled, unadjusted.
            if source == 'GHCN_QCU':
                data_path = 'data/GHCN_V4/ghcnm.tavg.v4.0.1.20200118.qcu.dat'
                data_type = Constants.DATA_TYPES['GHCN_QCU']
                # Quality controlled, adjusted.
            elif source == 'GHCN_QCF':
                data_path = 'data/GHCN_V4/ghcnm.tavg.v4.0.1.20200119.qcf.dat'
                data_type = Constants.DATA_TYPES['GHCN_QCF']
            # Quality controlled, adjusted and estimated.
            elif source == 'GHCN_QFE':
                data_path = 'data/GHCN_V4/ghcnm.tavg.v4.0.1.20200119.qfe.dat'
                data_type = Constants.DATA_TYPES['GHCN_QFE']

            print('Loading data file %s ... ' % data_path, end='')
            start_time = time.time()

            self.all_data = pd.read_csv(data_path, sep='\\s+', engine='python', header=None)
            self.all_data.replace('-9999', '', inplace=True)
            # Break 1st column into 2 columns: Station name and year.
            name_year = self.all_data.iloc[:, 0]
            name = name_year.str[:-4]
            year = name_year.str[-4:]
            self.all_data.drop(0, inplace=True, axis=1)
            self.all_data.insert(0, 'Year', year)
            self.all_data.Year = pd.to_numeric(self.all_data.Year, errors='coerce')
            self.all_data.insert(0, 'Name', name)

            self.data_type = data_type

            # Assign column headers.
            cols = ['Name', 'Year']
            for m in Constants.MONTHS:
                cols += [m, m + '_status']
            self.all_data.columns = cols

            # Measurements are in 100ths of degrees.
            for m in Constants.MONTHS:
                self.all_data[m] = self.all_data[m].replace('-9999', 'None')
                self.all_data[m] = pd.to_numeric(self.all_data[m], errors='coerce') / 100.

            print('Completed in ' + str(round(time.time()-start_time, 2)) + ' seconds')

        else:
            raise (ValueError('Unknown source type: ' + source))

if __name__ == '__main__':
    w = World()
    w.load_data('GHCN_QCU')
    # This example will plot the average temperature across the US per year.
    w.get_monthly_average(year_range=(1900, 2018), verbose=True, code='US', min_coverage=0, full_range=True)
    w.plot_data('Annual')
