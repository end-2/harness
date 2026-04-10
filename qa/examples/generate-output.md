# 테스트 코드 생성 출력 예시

> 휴가 관리 시스템 — FR-002(휴가 신청), FR-008(취소/수정) 테스트 스위트

---

## 테스트 스위트

```yaml
- id: TS-002
  type: unit
  title: "휴가 신청 서비스 단위 테스트"
  target_module: src/main/java/com/company/leave/service/
  framework: JUnit5
  test_cases:
    - case_id: TS-002-C01
      description: "유효한 연차 신청이 성공하고 '대기중' 상태로 저장된다"
      given: "잔여 연차 10일, 유효한 신청 정보 (연차, 내일~모레, 사유 입력)"
      when: "requestLeave를 호출"
      then: "신청이 저장되고 상태가 PENDING이다"
      technique: equivalence_partition
      acceptance_criteria_ref: "FR-002.AC-5"

    - case_id: TS-002-C02
      description: "반차(오전/오후) 유형을 선택하여 신청할 수 있다"
      given: "잔여 연차 5일"
      when: "반차(오전) 유형으로 requestLeave를 호출"
      then: "0.5일이 차감된 신청이 저장된다"
      technique: equivalence_partition
      acceptance_criteria_ref: "FR-002.AC-1"

    - case_id: TS-002-C03
      description: "병가, 특별휴가 유형도 신청 가능하다"
      given: "잔여 병가 3일"
      when: "병가 유형으로 requestLeave를 호출"
      then: "병가 잔여일수에서 차감된 신청이 저장된다"
      technique: equivalence_partition
      acceptance_criteria_ref: "FR-002.AC-1"

    - case_id: TS-002-C04
      description: "시작일이 오늘 이전이면 신청이 거부된다"
      given: "어제 날짜를 시작일로 설정"
      when: "requestLeave를 호출"
      then: "InvalidDateException 발생"
      technique: boundary_value
      acceptance_criteria_ref: "FR-002.AC-3"

    - case_id: TS-002-C05
      description: "시작일이 오늘이면 신청이 거부된다"
      given: "오늘 날짜를 시작일로 설정"
      when: "requestLeave를 호출"
      then: "InvalidDateException 발생 (경계값: 오늘은 '오늘 이후'에 해당하지 않음)"
      technique: boundary_value
      acceptance_criteria_ref: "FR-002.AC-3"

    - case_id: TS-002-C06
      description: "시작일이 내일이면 신청이 성공한다"
      given: "내일 날짜를 시작일로 설정, 잔여 연차 충분"
      when: "requestLeave를 호출"
      then: "신청 성공 (경계값: 최소 유효 시작일)"
      technique: boundary_value
      acceptance_criteria_ref: "FR-002.AC-3"

    - case_id: TS-002-C07
      description: "잔여 휴가 0일일 때 신청이 차단된다"
      given: "잔여 연차 0일"
      when: "연차 1일 requestLeave를 호출"
      then: "InsufficientBalanceException 발생, 안내 메시지 포함"
      technique: boundary_value
      acceptance_criteria_ref: "FR-002.AC-4"

    - case_id: TS-002-C08
      description: "잔여 휴가 1일일 때 1일 신청이 성공한다"
      given: "잔여 연차 1일"
      when: "연차 1일 requestLeave를 호출"
      then: "신청 성공 (경계값: 잔여 == 요청)"
      technique: boundary_value
      acceptance_criteria_ref: "FR-002.AC-4"

    - case_id: TS-002-C09
      description: "잔여 휴가 1일일 때 2일 신청이 차단된다"
      given: "잔여 연차 1일"
      when: "연차 2일 requestLeave를 호출"
      then: "InsufficientBalanceException 발생"
      technique: boundary_value
      acceptance_criteria_ref: "FR-002.AC-4"

    - case_id: TS-002-C10
      description: "Strategy 패턴: 연차 정책이 올바르게 적용된다"
      given: "연차 유형으로 신청"
      when: "requestLeave를 호출"
      then: "AnnualLeavePolicy.calculate()가 호출되어 일수 차감"
      technique: equivalence_partition
      acceptance_criteria_ref: "FR-002.AC-1"

    - case_id: TS-002-C11
      description: "Strategy 패턴: 병가 정책이 올바르게 적용된다"
      given: "병가 유형으로 신청"
      when: "requestLeave를 호출"
      then: "SickLeavePolicy.calculate()가 호출되어 일수 차감"
      technique: equivalence_partition
      acceptance_criteria_ref: "FR-002.AC-1"

  re_refs: [FR-002]
  arch_refs: [COMP-002]
  impl_refs: [IM-002, IDR-002]

- id: TS-008
  type: unit
  title: "휴가 취소/수정 서비스 단위 테스트"
  target_module: src/main/java/com/company/leave/service/
  framework: JUnit5
  test_cases:
    - case_id: TS-008-C01
      description: "대기중 상태의 신청 건을 취소할 수 있다"
      given: "상태가 PENDING인 신청 건"
      when: "cancelLeave를 호출"
      then: "상태가 CANCELLED로 변경, 잔여 일수 복원"
      technique: state_transition
      acceptance_criteria_ref: "FR-008.AC-1"

    - case_id: TS-008-C02
      description: "승인됨 상태의 신청 건은 직접 취소 불가"
      given: "상태가 APPROVED인 신청 건"
      when: "cancelLeave를 호출"
      then: "DirectCancelNotAllowedException 발생"
      technique: state_transition
      acceptance_criteria_ref: "FR-008.AC-1"

    - case_id: TS-008-C03
      description: "승인된 신청 건의 취소는 팀장에게 취소 요청 전달"
      given: "상태가 APPROVED인 신청 건"
      when: "requestCancellation을 호출"
      then: "취소 요청이 생성되고 팀장에게 알림 발송"
      technique: state_transition
      acceptance_criteria_ref: "FR-008.AC-2"

    - case_id: TS-008-C04
      description: "반려됨 상태의 신청 건은 수정 불가"
      given: "상태가 REJECTED인 신청 건"
      when: "modifyLeave를 호출"
      then: "ModificationNotAllowedException 발생"
      technique: state_transition
      acceptance_criteria_ref: "FR-008.AC-1"

    - case_id: TS-008-C05
      description: "대기중 상태의 신청 건을 수정하면 변경 이력이 기록된다"
      given: "상태가 PENDING인 신청 건, 종료일을 변경"
      when: "modifyLeave를 호출"
      then: "신청 건이 수정되고 ModificationHistory에 변경 전/후 값이 기록된다"
      technique: state_transition
      acceptance_criteria_ref: "FR-008.AC-3"

    - case_id: TS-008-C06
      description: "수정 시 변경 이력에 변경자, 시각, 변경 필드가 기록된다"
      given: "PENDING 신청 건, 사유를 변경"
      when: "modifyLeave를 호출"
      then: "ModificationHistory에 modifier, timestamp, changedField, oldValue, newValue가 기록된다"
      technique: equivalence_partition
      acceptance_criteria_ref: "FR-008.AC-3"

  re_refs: [FR-008]
  arch_refs: [COMP-002]
  impl_refs: [IM-002]
```

---

## 테스트 코드 (발췌)

### TS-002: LeaveServiceTest.java

```java
// @re_ref: FR-002
// @arch_ref: COMP-002
// @impl_ref: IM-002, IDR-002
@ExtendWith(MockitoExtension.class)
class LeaveServiceTest {

    @Spy
    private LeaveRepository leaveRepository;

    @Mock
    private LeaveBalanceService balanceService;

    @InjectMocks
    private LeaveService leaveService;

    // @acceptance_criteria_ref: FR-002.AC-5
    @Test
    void should_saveLeaveWithPendingStatus_when_validRequest() {
        // Arrange
        LeaveRequest request = LeaveRequest.builder()
            .type(LeaveType.ANNUAL)
            .startDate(LocalDate.now().plusDays(1))
            .endDate(LocalDate.now().plusDays(2))
            .reason("개인 사유")
            .employeeId("EMP-001")
            .build();
        when(balanceService.getRemainingDays("EMP-001", LeaveType.ANNUAL))
            .thenReturn(10);

        // Act
        LeaveApplication result = leaveService.requestLeave(request);

        // Assert
        assertThat(result.getStatus()).isEqualTo(LeaveStatus.PENDING);
        verify(leaveRepository).save(any(LeaveApplication.class));
    }

    // @acceptance_criteria_ref: FR-002.AC-3
    @Test
    void should_throwInvalidDateException_when_startDateIsToday() {
        // Arrange
        LeaveRequest request = LeaveRequest.builder()
            .type(LeaveType.ANNUAL)
            .startDate(LocalDate.now())  // 경계값: 오늘
            .endDate(LocalDate.now().plusDays(1))
            .reason("사유")
            .employeeId("EMP-001")
            .build();

        // Act & Assert
        assertThatThrownBy(() -> leaveService.requestLeave(request))
            .isInstanceOf(InvalidDateException.class)
            .hasMessageContaining("시작일은 오늘 이후");
    }

    // @acceptance_criteria_ref: FR-002.AC-4
    @Test
    void should_throwInsufficientBalanceException_when_balanceIsZero() {
        // Arrange
        LeaveRequest request = LeaveRequest.builder()
            .type(LeaveType.ANNUAL)
            .startDate(LocalDate.now().plusDays(1))
            .endDate(LocalDate.now().plusDays(1))
            .reason("사유")
            .employeeId("EMP-001")
            .build();
        when(balanceService.getRemainingDays("EMP-001", LeaveType.ANNUAL))
            .thenReturn(0);

        // Act & Assert
        assertThatThrownBy(() -> leaveService.requestLeave(request))
            .isInstanceOf(InsufficientBalanceException.class);
    }

    // @acceptance_criteria_ref: FR-002.AC-4
    @Test
    void should_succeedLeaveRequest_when_balanceEqualsRequestedDays() {
        // Arrange
        LeaveRequest request = LeaveRequest.builder()
            .type(LeaveType.ANNUAL)
            .startDate(LocalDate.now().plusDays(1))
            .endDate(LocalDate.now().plusDays(1))  // 1일
            .reason("사유")
            .employeeId("EMP-001")
            .build();
        when(balanceService.getRemainingDays("EMP-001", LeaveType.ANNUAL))
            .thenReturn(1);  // 경계값: 잔여 == 요청

        // Act
        LeaveApplication result = leaveService.requestLeave(request);

        // Assert
        assertThat(result.getStatus()).isEqualTo(LeaveStatus.PENDING);
    }
}
```

### TS-008: LeaveCancellationTest.java

```java
// @re_ref: FR-008
// @arch_ref: COMP-002
// @impl_ref: IM-002
@ExtendWith(MockitoExtension.class)
class LeaveCancellationTest {

    @Spy
    private LeaveRepository leaveRepository;

    @Mock
    private NotificationService notificationService;

    @InjectMocks
    private LeaveService leaveService;

    // @acceptance_criteria_ref: FR-008.AC-1
    @Test
    void should_cancelLeave_when_statusIsPending() {
        // Arrange
        LeaveApplication app = createApplication(LeaveStatus.PENDING);
        when(leaveRepository.findById(app.getId())).thenReturn(Optional.of(app));

        // Act
        leaveService.cancelLeave(app.getId());

        // Assert
        assertThat(app.getStatus()).isEqualTo(LeaveStatus.CANCELLED);
    }

    // @acceptance_criteria_ref: FR-008.AC-1
    @Test
    void should_throwException_when_cancelApprovedLeaveDirectly() {
        // Arrange
        LeaveApplication app = createApplication(LeaveStatus.APPROVED);
        when(leaveRepository.findById(app.getId())).thenReturn(Optional.of(app));

        // Act & Assert
        assertThatThrownBy(() -> leaveService.cancelLeave(app.getId()))
            .isInstanceOf(DirectCancelNotAllowedException.class);
    }

    // @acceptance_criteria_ref: FR-008.AC-3
    @Test
    void should_recordModificationHistory_when_modifyPendingLeave() {
        // Arrange
        LeaveApplication app = createApplication(LeaveStatus.PENDING);
        when(leaveRepository.findById(app.getId())).thenReturn(Optional.of(app));
        LocalDate newEndDate = app.getEndDate().plusDays(1);

        // Act
        leaveService.modifyLeave(app.getId(), ModifyRequest.builder()
            .endDate(newEndDate)
            .build());

        // Assert
        assertThat(app.getModificationHistory()).hasSize(1);
        ModificationRecord record = app.getModificationHistory().get(0);
        assertThat(record.getChangedField()).isEqualTo("endDate");
        assertThat(record.getOldValue()).isNotEqualTo(record.getNewValue());
        assertThat(record.getTimestamp()).isNotNull();
    }
}
```
