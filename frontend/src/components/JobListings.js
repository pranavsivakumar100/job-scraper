import React, { useState } from 'react';
import {
  Container,
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Button,
  Pagination,
  CircularProgress,
  Alert,
} from '@mui/material';
import {
  Search as SearchIcon,
  LocationOn as LocationIcon,
  Business as BusinessIcon,
  Work as WorkIcon,
  AccessTime as TimeIcon,
  Clear as ClearIcon,
} from '@mui/icons-material';
import { useQuery } from 'react-query';
import { Link } from 'react-router-dom';
import { format } from 'date-fns';
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || (process.env.NODE_ENV === 'production' ? 'http://localhost:8000' : '');

const JobListings = () => {
  const [filters, setFilters] = useState({
    search: '',
    company: '',
    location: '',
    remote_type: '',
    department: '',
    experience_level: '',
    employment_type: '',
    salary_min: '',
    salary_max: '',
  });
  const [page, setPage] = useState(1);
  const [perPage] = useState(20);

  // Fetch available companies
  const { data: companiesData } = useQuery(
    'companies',
    async () => {
      const response = await axios.get(`${API_BASE_URL}/companies`);
      return response.data;
    }
  );

  // Fetch filter statistics
  const { data: filterStats } = useQuery(
    ['filterStats', filters.company],
    async () => {
      const params = new URLSearchParams();
      if (filters.company) {
        params.append('company', filters.company);
      }
      const response = await axios.get(`${API_BASE_URL}/stats/filters?${params}`);
      return response.data;
    }
  );

  // Fetch jobs with current filters
  const { data: jobsData, isLoading, error } = useQuery(
    ['jobs', filters, page],
    async () => {
      const params = new URLSearchParams({
        page: page.toString(),
        per_page: perPage.toString(),
        ...Object.fromEntries(Object.entries(filters).filter(([_, v]) => v !== '')),
      });
      
      const response = await axios.get(`${API_BASE_URL}/jobs?${params}`);
      return response.data;
    },
    {
      keepPreviousData: true,
    }
  );

  const handleFilterChange = (field, value) => {
    setFilters(prev => ({ ...prev, [field]: value }));
    setPage(1); // Reset to first page when filtering
  };

  const clearFilters = () => {
    setFilters({
      search: '',
      company: '',
      location: '',
      remote_type: '',
      department: '',
      experience_level: '',
      employment_type: '',
      salary_min: '',
      salary_max: '',
    });
    setPage(1);
  };

  const formatSalary = (min, max, currency = 'USD') => {
    const formatter = new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    });

    if (min && max) {
      return `${formatter.format(min)} - ${formatter.format(max)}`;
    } else if (min) {
      return `${formatter.format(min)}+`;
    } else if (max) {
      return `Up to ${formatter.format(max)}`;
    }
    return 'Salary not disclosed';
  };

  const getRemoteTypeColor = (type) => {
    switch (type) {
      case 'Remote': return 'success';
      case 'Hybrid': return 'warning';
      case 'On-site': return 'info';
      default: return 'default';
    }
  };

  const getExperienceColor = (level) => {
    switch (level) {
      case 'Internship': return 'secondary';
      case 'Entry': return 'primary';
      case 'Mid': return 'info';
      case 'Senior': return 'warning';
      case 'Principal': return 'error';
      default: return 'default';
    }
  };

  // Get selected company name for display
  const selectedCompanyName = filters.company || 'All Companies';
  const totalJobs = jobsData?.total || 0;

  if (error) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Alert severity="error">
          Error loading jobs: {error.message}
        </Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Tech Job Listings
        </Typography>
        <Typography variant="subtitle1" color="text.secondary">
          {totalJobs} opportunities from {selectedCompanyName === 'All Companies' ? 'top tech companies' : selectedCompanyName} with accurate posting dates
        </Typography>
      </Box>

      {/* Filters */}
      <Card sx={{ mb: 4, p: 3 }}>
        <Grid container spacing={3}>
          {/* Search */}
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Search jobs"
              placeholder="Search by title, department, or keywords..."
              value={filters.search}
              onChange={(e) => handleFilterChange('search', e.target.value)}
              InputProps={{
                startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />,
              }}
            />
          </Grid>

          {/* Company */}
          <Grid item xs={12} md={3}>
            <FormControl fullWidth>
              <InputLabel>Company</InputLabel>
              <Select
                value={filters.company}
                label="Company"
                onChange={(e) => handleFilterChange('company', e.target.value)}
              >
                <MenuItem value="">All Companies</MenuItem>
                {companiesData?.companies?.map((company) => (
                  <MenuItem key={company.name} value={company.name}>
                    {company.name} ({company.count})
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>

          {/* Location */}
          <Grid item xs={12} md={3}>
            <FormControl fullWidth>
              <InputLabel>Location</InputLabel>
              <Select
                value={filters.location}
                label="Location"
                onChange={(e) => handleFilterChange('location', e.target.value)}
              >
                <MenuItem value="">All Locations</MenuItem>
                {filterStats?.locations?.map((location) => (
                  <MenuItem key={location.name} value={location.name}>
                    {location.name} ({location.count})
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>

          {/* Remote Type */}
          <Grid item xs={12} md={4}>
            <FormControl fullWidth>
              <InputLabel>Remote Type</InputLabel>
              <Select
                value={filters.remote_type}
                label="Remote Type"
                onChange={(e) => handleFilterChange('remote_type', e.target.value)}
              >
                <MenuItem value="">All Types</MenuItem>
                {filterStats?.remote_types?.map((type) => (
                  <MenuItem key={type.name} value={type.name}>
                    {type.name} ({type.count})
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>

          {/* Experience Level */}
          <Grid item xs={12} md={4}>
            <FormControl fullWidth>
              <InputLabel>Experience Level</InputLabel>
              <Select
                value={filters.experience_level}
                label="Experience Level"
                onChange={(e) => handleFilterChange('experience_level', e.target.value)}
              >
                <MenuItem value="">All Levels</MenuItem>
                {filterStats?.experience_levels?.map((level) => (
                  <MenuItem key={level.name} value={level.name}>
                    {level.name} ({level.count})
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>

          {/* Employment Type */}
          <Grid item xs={12} md={4}>
            <FormControl fullWidth>
              <InputLabel>Employment Type</InputLabel>
              <Select
                value={filters.employment_type}
                label="Employment Type"
                onChange={(e) => handleFilterChange('employment_type', e.target.value)}
              >
                <MenuItem value="">All Types</MenuItem>
                {filterStats?.employment_types?.map((type) => (
                  <MenuItem key={type.name} value={type.name}>
                    {type.name} ({type.count})
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>

          {/* Clear Filters */}
          <Grid item xs={12}>
            <Button
              variant="outlined"
              startIcon={<ClearIcon />}
              onClick={clearFilters}
              sx={{ mt: 1 }}
            >
              Clear All Filters
            </Button>
          </Grid>
        </Grid>
      </Card>

      {/* Loading */}
      {isLoading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
          <CircularProgress />
        </Box>
      )}

      {/* Job Results */}
      {jobsData && (
        <>
          <Grid container spacing={3}>
            {jobsData.jobs.map((job) => (
              <Grid item xs={12} key={job.id}>
                <Card 
                  component={Link}
                  to={`/jobs/${job.id}`}
                  sx={{ 
                    textDecoration: 'none',
                    transition: 'transform 0.2s',
                    '&:hover': {
                      transform: 'translateY(-2px)',
                    }
                  }}
                >
                  <CardContent>
                    <Grid container spacing={2}>
                      <Grid item xs={12} md={8}>
                        <Typography variant="h6" component="h2" gutterBottom>
                          {job.title}
                        </Typography>
                        
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
                          <Chip
                            icon={<BusinessIcon />}
                            label={job.company}
                            size="small"
                            variant="outlined"
                          />
                          {job.location && (
                            <Chip
                              icon={<LocationIcon />}
                              label={job.location}
                              size="small"
                              variant="outlined"
                            />
                          )}
                          {job.remote_type && (
                            <Chip
                              label={job.remote_type}
                              size="small"
                              color={getRemoteTypeColor(job.remote_type)}
                            />
                          )}
                          {job.experience_level && (
                            <Chip
                              label={job.experience_level}
                              size="small"
                              color={getExperienceColor(job.experience_level)}
                            />
                          )}
                          {job.employment_type && (
                            <Chip
                              icon={<WorkIcon />}
                              label={job.employment_type}
                              size="small"
                              variant="outlined"
                            />
                          )}
                        </Box>

                        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                          {job.description && job.description !== 'Sign in' && !job.description.includes('u0040') ? 
                            `${job.description.substring(0, 200)}${job.description.length > 200 ? '...' : ''}` 
                            : 'Job description not available - click to view on company website'
                          }
                        </Typography>
                      </Grid>

                      <Grid item xs={12} md={4}>
                        <Box sx={{ textAlign: { xs: 'left', md: 'right' } }}>
                          {(job.salary_min || job.salary_max) && (
                            <Typography variant="h6" color="primary" gutterBottom>
                              {formatSalary(job.salary_min, job.salary_max, job.salary_currency)}
                            </Typography>
                          )}
                          
                          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: { xs: 'flex-start', md: 'flex-end' } }}>
                            <TimeIcon sx={{ mr: 0.5, fontSize: 16, color: 'text.secondary' }} />
                            <Typography variant="body2" color="text.secondary">
                              {job.posted_date ? format(new Date(job.posted_date), 'MMM d, yyyy') : 'Date not available'}
                            </Typography>
                          </Box>
                        </Box>
                      </Grid>
                    </Grid>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>

          {/* Pagination */}
          {jobsData.total_pages > 1 && (
            <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
              <Pagination
                count={jobsData.total_pages}
                page={page}
                onChange={(event, value) => setPage(value)}
                color="primary"
                size="large"
              />
            </Box>
          )}
        </>
      )}
    </Container>
  );
};

export default JobListings; 