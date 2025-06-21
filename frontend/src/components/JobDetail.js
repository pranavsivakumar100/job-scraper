import React from 'react';
import {
  Container,
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  Button,
  Divider,
  Grid,
  CircularProgress,
  Alert,
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  OpenInNew as OpenInNewIcon,
  LocationOn as LocationIcon,
  Business as BusinessIcon,
  Work as WorkIcon,
  AccessTime as TimeIcon,
  AttachMoney as MoneyIcon,
} from '@mui/icons-material';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from 'react-query';
import { format } from 'date-fns';
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const JobDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();

  const { data: job, isLoading, error } = useQuery(
    ['job', id],
    async () => {
      const response = await axios.get(`${API_BASE_URL}/jobs/${id}`);
      return response.data;
    }
  );

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

  if (isLoading) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  if (error) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Alert severity="error">
          Error loading job details: {error.message}
        </Alert>
      </Container>
    );
  }

  if (!job) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Alert severity="info">
          Job not found
        </Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      {/* Back Button */}
      <Button
        startIcon={<ArrowBackIcon />}
        onClick={() => navigate(-1)}
        sx={{ mb: 3 }}
      >
        Back to Jobs
      </Button>

      <Grid container spacing={4}>
        {/* Main Content */}
        <Grid item xs={12} lg={8}>
          <Card>
            <CardContent sx={{ p: 4 }}>
              {/* Header */}
              <Box sx={{ mb: 3 }}>
                <Typography variant="h4" component="h1" gutterBottom>
                  {job.title}
                </Typography>
                
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
                  <Chip
                    icon={<BusinessIcon />}
                    label={job.company}
                    size="medium"
                    color="primary"
                  />
                  {job.location && (
                    <Chip
                      icon={<LocationIcon />}
                      label={job.location}
                      size="medium"
                      variant="outlined"
                    />
                  )}
                  {job.remote_type && (
                    <Chip
                      label={job.remote_type}
                      size="medium"
                      color={getRemoteTypeColor(job.remote_type)}
                    />
                  )}
                  {job.experience_level && (
                    <Chip
                      label={job.experience_level}
                      size="medium"
                      color={getExperienceColor(job.experience_level)}
                    />
                  )}
                  {job.employment_type && (
                    <Chip
                      icon={<WorkIcon />}
                      label={job.employment_type}
                      size="medium"
                      variant="outlined"
                    />
                  )}
                </Box>
              </Box>

              <Divider sx={{ my: 3 }} />

              {/* Job Description */}
              <Box sx={{ mb: 4 }}>
                <Typography variant="h6" gutterBottom>
                  Job Description
                </Typography>
                <Typography variant="body1" sx={{ lineHeight: 1.8, whiteSpace: 'pre-wrap' }}>
                  {job.description && job.description !== 'Sign in' && !job.description.includes('u0040') ? 
                    job.description : 'Description not available. Please visit the company website to view full job details.'
                  }
                </Typography>
              </Box>

              {/* Requirements */}
              {job.requirements && (
                <Box sx={{ mb: 4 }}>
                  <Typography variant="h6" gutterBottom>
                    Requirements
                  </Typography>
                  <Typography variant="body1" sx={{ lineHeight: 1.8, whiteSpace: 'pre-wrap' }}>
                    {job.requirements}
                  </Typography>
                </Box>
              )}

              {/* Benefits */}
              {job.benefits && (
                <Box sx={{ mb: 4 }}>
                  <Typography variant="h6" gutterBottom>
                    Benefits
                  </Typography>
                  <Typography variant="body1" sx={{ lineHeight: 1.8, whiteSpace: 'pre-wrap' }}>
                    {job.benefits}
                  </Typography>
                </Box>
              )}

              {/* Apply Button */}
              <Box sx={{ mt: 4 }}>
                <Button
                  variant="contained"
                  size="large"
                  endIcon={<OpenInNewIcon />}
                  href={job.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  sx={{ mr: 2 }}
                >
                  Apply on Company Website
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Sidebar */}
        <Grid item xs={12} lg={4}>
          <Card>
            <CardContent sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Job Details
              </Typography>

              <Box sx={{ mb: 3 }}>
                {(job.salary_min || job.salary_max) && (
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <MoneyIcon sx={{ mr: 1, color: 'text.secondary' }} />
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        Salary
                      </Typography>
                      <Typography variant="body1" fontWeight="medium">
                        {formatSalary(job.salary_min, job.salary_max, job.salary_currency)}
                      </Typography>
                    </Box>
                  </Box>
                )}

                {job.department && (
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <BusinessIcon sx={{ mr: 1, color: 'text.secondary' }} />
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        Department
                      </Typography>
                      <Typography variant="body1" fontWeight="medium">
                        {job.department}
                      </Typography>
                    </Box>
                  </Box>
                )}

                {job.posted_date && (
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <TimeIcon sx={{ mr: 1, color: 'text.secondary' }} />
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        Posted
                      </Typography>
                      <Typography variant="body1" fontWeight="medium">
                        {format(new Date(job.posted_date), 'MMMM dd, yyyy')}
                      </Typography>
                    </Box>
                  </Box>
                )}
              </Box>

              <Divider sx={{ my: 3 }} />

              <Button
                variant="outlined"
                fullWidth
                size="large"
                endIcon={<OpenInNewIcon />}
                href={job.url}
                target="_blank"
                rel="noopener noreferrer"
              >
                View Original Posting
              </Button>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
};

export default JobDetail; 