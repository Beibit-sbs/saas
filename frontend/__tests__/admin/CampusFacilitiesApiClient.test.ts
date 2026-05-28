import { beforeEach, describe, expect, it, vi } from 'vitest';

const client = vi.hoisted(() => ({
  apiGet: vi.fn(),
  apiPost: vi.fn(),
}));

vi.mock('@/shared/api/client', () => client);

import { campusFacilitiesApi, CAMPUS_FACILITIES_API_PATHS } from '@/modules/campus-facilities/api';

describe('Campus Facilities API client', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    client.apiGet.mockResolvedValue(undefined);
    client.apiPost.mockResolvedValue(undefined);
  });

  it('maps core reads', async () => {
    await campusFacilitiesApi.getOverview();
    await campusFacilitiesApi.getDashboard();
    await campusFacilitiesApi.getMetadataContract();
    await campusFacilitiesApi.getSafetyBoundaries();
    await campusFacilitiesApi.getHealth();

    expect(client.apiGet).toHaveBeenCalledWith(CAMPUS_FACILITIES_API_PATHS.overview);
    expect(client.apiGet).toHaveBeenCalledWith(CAMPUS_FACILITIES_API_PATHS.dashboard);
    expect(client.apiGet).toHaveBeenCalledWith(CAMPUS_FACILITIES_API_PATHS.metadataContract);
    expect(client.apiGet).toHaveBeenCalledWith(CAMPUS_FACILITIES_API_PATHS.safetyBoundaries);
    expect(client.apiGet).toHaveBeenCalledWith(CAMPUS_FACILITIES_API_PATHS.health);
  });

  it('maps facility reads', async () => {
    await campusFacilitiesApi.getCampus();
    await campusFacilitiesApi.getFacilities();
    await campusFacilitiesApi.getBuildings();
    await campusFacilitiesApi.getFloors();
    await campusFacilitiesApi.getRooms();
    await campusFacilitiesApi.getRoomTypes();
    await campusFacilitiesApi.getAvailability();
    await campusFacilitiesApi.getOccupancy();
    await campusFacilitiesApi.getDormitories();
    await campusFacilitiesApi.getHousingUnits();
    await campusFacilitiesApi.getHousingRequests();

    expect(client.apiGet).toHaveBeenCalledWith(CAMPUS_FACILITIES_API_PATHS.campus);
    expect(client.apiGet).toHaveBeenCalledWith(CAMPUS_FACILITIES_API_PATHS.facilities);
    expect(client.apiGet).toHaveBeenCalledWith(CAMPUS_FACILITIES_API_PATHS.buildings);
    expect(client.apiGet).toHaveBeenCalledWith(CAMPUS_FACILITIES_API_PATHS.floors);
    expect(client.apiGet).toHaveBeenCalledWith(CAMPUS_FACILITIES_API_PATHS.rooms);
    expect(client.apiGet).toHaveBeenCalledWith(CAMPUS_FACILITIES_API_PATHS.roomTypes);
    expect(client.apiGet).toHaveBeenCalledWith(CAMPUS_FACILITIES_API_PATHS.availability);
    expect(client.apiGet).toHaveBeenCalledWith(CAMPUS_FACILITIES_API_PATHS.occupancy);
    expect(client.apiGet).toHaveBeenCalledWith(CAMPUS_FACILITIES_API_PATHS.dormitories);
    expect(client.apiGet).toHaveBeenCalledWith(CAMPUS_FACILITIES_API_PATHS.housingUnits);
    expect(client.apiGet).toHaveBeenCalledWith(CAMPUS_FACILITIES_API_PATHS.housingRequests);
  });

  it('maps operations reads', async () => {
    await campusFacilitiesApi.getMaintenance();
    await campusFacilitiesApi.getServiceRequests();
    await campusFacilitiesApi.getWorkOrders();
    await campusFacilitiesApi.getTransportRoutes();
    await campusFacilitiesApi.getTransportVehicles();
    await campusFacilitiesApi.getTransportSchedules();
    await campusFacilitiesApi.getResponsibleUnits();
    await campusFacilitiesApi.getSafetyReadiness();
    await campusFacilitiesApi.getAuditEvidence();
    await campusFacilitiesApi.getLimitations();

    expect(client.apiGet).toHaveBeenCalledWith(CAMPUS_FACILITIES_API_PATHS.maintenance);
    expect(client.apiGet).toHaveBeenCalledWith(CAMPUS_FACILITIES_API_PATHS.serviceRequests);
    expect(client.apiGet).toHaveBeenCalledWith(CAMPUS_FACILITIES_API_PATHS.workOrders);
    expect(client.apiGet).toHaveBeenCalledWith(CAMPUS_FACILITIES_API_PATHS.transportRoutes);
    expect(client.apiGet).toHaveBeenCalledWith(CAMPUS_FACILITIES_API_PATHS.transportVehicles);
    expect(client.apiGet).toHaveBeenCalledWith(CAMPUS_FACILITIES_API_PATHS.transportSchedules);
    expect(client.apiGet).toHaveBeenCalledWith(CAMPUS_FACILITIES_API_PATHS.responsibleUnits);
    expect(client.apiGet).toHaveBeenCalledWith(CAMPUS_FACILITIES_API_PATHS.safetyReadiness);
    expect(client.apiGet).toHaveBeenCalledWith(CAMPUS_FACILITIES_API_PATHS.auditEvidence);
    expect(client.apiGet).toHaveBeenCalledWith(CAMPUS_FACILITIES_API_PATHS.limitations);
  });

  it('maps bridge reads', async () => {
    await campusFacilitiesApi.getAccessVisitorBridge();
    await campusFacilitiesApi.getStudentServicesBridge();
    await campusFacilitiesApi.getFinanceAssetBridge();
    await campusFacilitiesApi.getHrStaffBridge();

    expect(client.apiGet).toHaveBeenCalledWith(CAMPUS_FACILITIES_API_PATHS.bridgeAccessVisitor);
    expect(client.apiGet).toHaveBeenCalledWith(CAMPUS_FACILITIES_API_PATHS.bridgeStudentServices);
    expect(client.apiGet).toHaveBeenCalledWith(CAMPUS_FACILITIES_API_PATHS.bridgeFinanceAsset);
    expect(client.apiGet).toHaveBeenCalledWith(CAMPUS_FACILITIES_API_PATHS.bridgeHrStaff);
  });

  it('maps metadata writes', async () => {
    await campusFacilitiesApi.submitFacilityMetadata({ a: 1 });
    await campusFacilitiesApi.submitBuildingMetadata({ a: 2 });
    await campusFacilitiesApi.submitFloorMetadata({ a: 3 });
    await campusFacilitiesApi.submitRoomMetadata({ a: 4 });
    await campusFacilitiesApi.submitAvailabilityMetadata({ a: 5 });
    await campusFacilitiesApi.submitOccupancyMetadata({ a: 6 });
    await campusFacilitiesApi.submitDormitoryMetadata({ a: 7 });
    await campusFacilitiesApi.submitHousingUnitMetadata({ a: 8 });
    await campusFacilitiesApi.submitHousingRequestMetadata({ a: 9 });
    await campusFacilitiesApi.submitMaintenanceMetadata({ a: 10 });
    await campusFacilitiesApi.submitServiceRequestMetadata({ a: 11 });
    await campusFacilitiesApi.submitWorkOrderMetadata({ a: 12 });

    expect(client.apiPost).toHaveBeenCalledWith(CAMPUS_FACILITIES_API_PATHS.facilityMetadata, { a: 1 });
    expect(client.apiPost).toHaveBeenCalledWith(CAMPUS_FACILITIES_API_PATHS.buildingMetadata, { a: 2 });
    expect(client.apiPost).toHaveBeenCalledWith(CAMPUS_FACILITIES_API_PATHS.floorMetadata, { a: 3 });
    expect(client.apiPost).toHaveBeenCalledWith(CAMPUS_FACILITIES_API_PATHS.roomMetadata, { a: 4 });
    expect(client.apiPost).toHaveBeenCalledWith(CAMPUS_FACILITIES_API_PATHS.availabilityMetadata, { a: 5 });
    expect(client.apiPost).toHaveBeenCalledWith(CAMPUS_FACILITIES_API_PATHS.occupancyMetadata, { a: 6 });
    expect(client.apiPost).toHaveBeenCalledWith(CAMPUS_FACILITIES_API_PATHS.dormitoryMetadata, { a: 7 });
    expect(client.apiPost).toHaveBeenCalledWith(CAMPUS_FACILITIES_API_PATHS.housingUnitMetadata, { a: 8 });
    expect(client.apiPost).toHaveBeenCalledWith(CAMPUS_FACILITIES_API_PATHS.housingRequestMetadata, { a: 9 });
    expect(client.apiPost).toHaveBeenCalledWith(CAMPUS_FACILITIES_API_PATHS.maintenanceMetadata, { a: 10 });
    expect(client.apiPost).toHaveBeenCalledWith(CAMPUS_FACILITIES_API_PATHS.serviceRequestMetadata, { a: 11 });
    expect(client.apiPost).toHaveBeenCalledWith(CAMPUS_FACILITIES_API_PATHS.workOrderMetadata, { a: 12 });
  });

  it('maps transport/bridge writes', async () => {
    await campusFacilitiesApi.submitTransportRouteMetadata({ t: 1 });
    await campusFacilitiesApi.submitTransportVehicleMetadata({ t: 2 });
    await campusFacilitiesApi.submitTransportScheduleMetadata({ t: 3 });
    await campusFacilitiesApi.submitResponsibleUnitMetadata({ t: 4 });
    await campusFacilitiesApi.submitSafetyReadinessEvidence({ t: 5 });
    await campusFacilitiesApi.submitAccessVisitorBridgeMetadata({ t: 6 });
    await campusFacilitiesApi.submitStudentServicesBridgeMetadata({ t: 7 });
    await campusFacilitiesApi.submitFinanceAssetBridgeMetadata({ t: 8 });
    await campusFacilitiesApi.submitHrStaffBridgeMetadata({ t: 9 });
    await campusFacilitiesApi.submitLimitationsMetadata({ t: 10 });

    expect(client.apiPost).toHaveBeenCalledWith(CAMPUS_FACILITIES_API_PATHS.transportRouteMetadata, { t: 1 });
    expect(client.apiPost).toHaveBeenCalledWith(CAMPUS_FACILITIES_API_PATHS.transportVehicleMetadata, { t: 2 });
    expect(client.apiPost).toHaveBeenCalledWith(CAMPUS_FACILITIES_API_PATHS.transportScheduleMetadata, { t: 3 });
    expect(client.apiPost).toHaveBeenCalledWith(CAMPUS_FACILITIES_API_PATHS.responsibleUnitMetadata, { t: 4 });
    expect(client.apiPost).toHaveBeenCalledWith(CAMPUS_FACILITIES_API_PATHS.safetyReadinessEvidence, { t: 5 });
    expect(client.apiPost).toHaveBeenCalledWith(CAMPUS_FACILITIES_API_PATHS.bridgeAccessVisitorMetadata, { t: 6 });
    expect(client.apiPost).toHaveBeenCalledWith(CAMPUS_FACILITIES_API_PATHS.bridgeStudentServicesMetadata, { t: 7 });
    expect(client.apiPost).toHaveBeenCalledWith(CAMPUS_FACILITIES_API_PATHS.bridgeFinanceAssetMetadata, { t: 8 });
    expect(client.apiPost).toHaveBeenCalledWith(CAMPUS_FACILITIES_API_PATHS.bridgeHrStaffMetadata, { t: 9 });
    expect(client.apiPost).toHaveBeenCalledWith(CAMPUS_FACILITIES_API_PATHS.limitationsMetadata, { t: 10 });
  });

  it('does not expose forbidden capability methods', () => {
    expect('enableLiveIot' in campusFacilitiesApi).toBe(false);
    expect('enableLiveGps' in campusFacilitiesApi).toBe(false);
    expect('enableBuildingAutomation' in campusFacilitiesApi).toBe(false);
    expect('enforceAccessControl' in campusFacilitiesApi).toBe(false);
    expect('certifySafety' in campusFacilitiesApi).toBe(false);
    expect('autonomousDispatch' in campusFacilitiesApi).toBe(false);
    expect('externalProviderSync' in campusFacilitiesApi).toBe(false);
    expect('productionFacilitiesClaim' in campusFacilitiesApi).toBe(false);
  });
});
