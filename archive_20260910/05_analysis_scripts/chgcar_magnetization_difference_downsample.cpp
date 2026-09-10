#include <algorithm>
#include <array>
#include <cctype>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <numeric>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

struct Header {
    std::array<std::array<double, 3>, 3> lattice{};
    std::array<int, 3> grid{};
    std::vector<int> counts;
};

static std::vector<std::string> split(const std::string &line) {
    std::istringstream stream(line);
    std::vector<std::string> fields;
    std::string field;
    while (stream >> field) fields.push_back(field);
    return fields;
}

static bool integer_token(const std::string &value) {
    if (value.empty()) return false;
    std::size_t start = (value[0] == '+' || value[0] == '-') ? 1 : 0;
    return start < value.size() &&
           std::all_of(value.begin() + static_cast<long>(start), value.end(), ::isdigit);
}

static Header read_header(std::ifstream &input) {
    Header header;
    std::string line;
    std::getline(input, line);
    std::getline(input, line);
    const double scale = std::stod(split(line).at(0));
    for (int row = 0; row < 3; ++row) {
        std::getline(input, line);
        const auto fields = split(line);
        for (int col = 0; col < 3; ++col) header.lattice[row][col] = scale * std::stod(fields.at(col));
    }

    std::getline(input, line);
    auto fields = split(line);
    if (!std::all_of(fields.begin(), fields.end(), integer_token)) {
        std::getline(input, line);
        fields = split(line);
    }
    for (const auto &field : fields) header.counts.push_back(std::stoi(field));

    std::getline(input, line);
    if (!line.empty() && (line[0] == 'S' || line[0] == 's')) std::getline(input, line);
    const int atoms = std::accumulate(header.counts.begin(), header.counts.end(), 0);
    for (int atom = 0; atom < atoms; ++atom) std::getline(input, line);

    while (std::getline(input, line)) {
        fields = split(line);
        if (fields.size() == 3 && std::all_of(fields.begin(), fields.end(), integer_token)) {
            for (int axis = 0; axis < 3; ++axis) header.grid[axis] = std::stoi(fields[axis]);
            return header;
        }
    }
    throw std::runtime_error("CHGCAR charge grid line not found");
}

static void seek_magnetization_grid(std::ifstream &input, const Header &header) {
    const std::int64_t points = static_cast<std::int64_t>(header.grid[0]) * header.grid[1] * header.grid[2];
    double value = 0.0;
    for (std::int64_t index = 0; index < points; ++index) {
        if (!(input >> value)) throw std::runtime_error("charge grid ended early");
    }

    std::string line;
    std::getline(input, line);
    while (std::getline(input, line)) {
        const auto fields = split(line);
        if (fields.size() != 3 || !std::all_of(fields.begin(), fields.end(), integer_token)) continue;
        if (std::stoi(fields[0]) == header.grid[0] &&
            std::stoi(fields[1]) == header.grid[1] &&
            std::stoi(fields[2]) == header.grid[2]) return;
    }
    throw std::runtime_error("CHGCAR magnetization grid line not found; ISPIN=2 data are required");
}

static double determinant(const std::array<std::array<double, 3>, 3> &m) {
    return m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1])
         - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0])
         + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0]);
}

int main(int argc, char **argv) {
    if (argc != 5) {
        std::cerr << "usage: " << argv[0] << " O_CHGCAR OH_CHGCAR OUTPUT_RAW DOWNSAMPLE\n";
        return 2;
    }
    const int downsample = std::stoi(argv[4]);
    if (downsample <= 0) throw std::runtime_error("downsample must be positive");

    std::ifstream oxygen(argv[1]);
    std::ifstream hydroxyl(argv[2]);
    if (!oxygen || !hydroxyl) throw std::runtime_error("failed to open an input CHGCAR");
    const Header oxygen_header = read_header(oxygen);
    const Header hydroxyl_header = read_header(hydroxyl);
    if (oxygen_header.grid != hydroxyl_header.grid) throw std::runtime_error("FFT grids differ");
    for (int row = 0; row < 3; ++row) {
        for (int col = 0; col < 3; ++col) {
            if (std::abs(oxygen_header.lattice[row][col] - hydroxyl_header.lattice[row][col]) > 1e-10)
                throw std::runtime_error("lattice vectors differ");
        }
    }

    seek_magnetization_grid(oxygen, oxygen_header);
    seek_magnetization_grid(hydroxyl, hydroxyl_header);

    const int nx = oxygen_header.grid[0];
    const int ny = oxygen_header.grid[1];
    const int nz = oxygen_header.grid[2];
    if (nx % downsample || ny % downsample || nz % downsample)
        throw std::runtime_error("downsample must divide all grid dimensions");
    const int ox = nx / downsample;
    const int oy = ny / downsample;
    const int oz = nz / downsample;
    const std::int64_t points = static_cast<std::int64_t>(nx) * ny * nz;
    const double volume = std::abs(determinant(oxygen_header.lattice));

    std::ofstream output(argv[3], std::ios::binary);
    if (!output) throw std::runtime_error("failed to open output");
    const char magic[8] = {'M','A','G','D','I','F','F','1'};
    const std::int32_t version = 1;
    const std::int32_t ds = downsample;
    const std::int32_t dims[3] = {ox, oy, oz};
    output.write(magic, sizeof(magic));
    output.write(reinterpret_cast<const char *>(&version), sizeof(version));
    output.write(reinterpret_cast<const char *>(&ds), sizeof(ds));
    output.write(reinterpret_cast<const char *>(dims), sizeof(dims));
    for (const auto &row : oxygen_header.lattice)
        output.write(reinterpret_cast<const char *>(row.data()), 3 * sizeof(double));
    output.write(reinterpret_cast<const char *>(&volume), sizeof(volume));

    double oxygen_value = 0.0;
    double hydroxyl_value = 0.0;
    double sum_raw = 0.0;
    float minimum = 1e30f;
    float maximum = -1e30f;
    std::int64_t written = 0;
    for (std::int64_t index = 0; index < points; ++index) {
        if (!(oxygen >> oxygen_value) || !(hydroxyl >> hydroxyl_value))
            throw std::runtime_error("magnetization grid ended early");
        const double raw_difference = oxygen_value - hydroxyl_value;
        sum_raw += raw_difference;
        const int x = static_cast<int>(index % nx);
        const int y = static_cast<int>((index / nx) % ny);
        const int z = static_cast<int>(index / (static_cast<std::int64_t>(nx) * ny));
        if (x % downsample == 0 && y % downsample == 0 && z % downsample == 0) {
            const float density = static_cast<float>(raw_difference / volume);
            output.write(reinterpret_cast<const char *>(&density), sizeof(density));
            minimum = std::min(minimum, density);
            maximum = std::max(maximum, density);
            ++written;
        }
    }
    output.close();
    std::cout << std::setprecision(12)
              << "input_grid=" << nx << 'x' << ny << 'x' << nz << '\n'
              << "output_grid=" << ox << 'x' << oy << 'x' << oz << '\n'
              << "volume_A3=" << volume << '\n'
              << "integrated_delta_m_muB=" << sum_raw / static_cast<double>(points) << '\n'
              << "magnetization_min_muB_A3=" << minimum << '\n'
              << "magnetization_max_muB_A3=" << maximum << '\n'
              << "written_points=" << written << '\n';
    return written == static_cast<std::int64_t>(ox) * oy * oz ? 0 : 3;
}
